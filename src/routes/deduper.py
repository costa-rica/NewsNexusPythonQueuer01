from flask import Blueprint, request, jsonify
import subprocess
import threading
import time
import os
from datetime import datetime, timezone
from loguru import logger
from ..utils.errors import error_response

bp_deduper = Blueprint('deduper', __name__)

# In-memory job storage (in production, use a database)
jobs = {}
# Simple counter for integer job IDs
job_counter = 1

class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

def create_job_id():
    global job_counter
    job_id = job_counter
    job_counter += 1
    return job_id

def run_deduper_job(job_id, report_id=None):
    """Run the deduper microservice in a separate thread"""
    try:
        jobs[job_id]['status'] = JobStatus.RUNNING
        jobs[job_id]['started_at'] = datetime.now(timezone.utc).isoformat()

        # Get deduper path from environment
        deduper_path = os.getenv('PATH_TO_MICROSERVICE_DEDUPER')
        python_venv = os.getenv('PATH_TO_PYTHON_VENV')

        if not deduper_path or not python_venv:
            raise Exception("Missing environment variables for deduper or python venv")

        # Build command to run deduper
        cmd = [
            f"{python_venv}/bin/python",
            f"{deduper_path}/src/main.py",
            "analyze_fast"
        ]

        # Add report_id argument if provided
        if report_id is not None:
            cmd.extend(["--report-id", str(report_id)])

        # CRITICAL: Get child process NAME_APP from environment variable
        child_process_name = os.getenv('NAME_CHILD_PROCESS_DEDUPER')
        if not child_process_name:
            raise ValueError("NAME_CHILD_PROCESS_DEDUPER environment variable is required")

        # Inject NAME_APP for child process to write to its own log file
        child_env = os.environ.copy()
        child_env['NAME_APP'] = child_process_name

        logger.info(f"[Job {job_id}] Starting deduper with NAME_APP={child_process_name}: {' '.join(cmd)}")

        # Run the subprocess with injected environment
        process = subprocess.Popen(
            cmd,
            env=child_env,
            text=True
        )

        jobs[job_id]['process'] = process

        # Wait for completion
        exit_code = process.wait()

        jobs[job_id]['exit_code'] = process.returncode
        jobs[job_id]['completed_at'] = datetime.now(timezone.utc).isoformat()

        if process.returncode == 0:
            jobs[job_id]['status'] = JobStatus.COMPLETED
            logger.info(f"[Job {job_id}] Deduper completed successfully with exit code 0")
        else:
            jobs[job_id]['status'] = JobStatus.FAILED
            logger.error(f"[Job {job_id}] Deduper failed with exit code {process.returncode}")

    except Exception as e:
        jobs[job_id]['status'] = JobStatus.FAILED
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['completed_at'] = datetime.now(timezone.utc).isoformat()
        logger.exception(f"[Job {job_id}] Deduper job failed with exception: {str(e)}")

@bp_deduper.route('/deduper/jobs', methods=['GET'])
def create_deduper_job():
    """GET /deduper/jobs - Trigger a deduper job and return { jobId, status }"""
    try:
        # Create new job
        job_id = create_job_id()
        jobs[job_id] = {
            'id': job_id,
            'status': JobStatus.PENDING,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'logs': []
        }

        logger.info(f"Created deduper job {job_id}")

        # Start job in background thread
        thread = threading.Thread(target=run_deduper_job, args=(job_id,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'jobId': job_id,
            'status': JobStatus.PENDING
        }), 201

    except Exception as e:
        logger.error(f"Failed to create deduper job: {str(e)}")
        return error_response(
            code='JOB_CREATION_FAILED',
            message='Failed to create deduper job',
            status=500,
            details=str(e)
        )

@bp_deduper.route('/deduper/jobs/reportId/<int:report_id>', methods=['GET'])
def create_deduper_job_by_report_id(report_id):
    """GET /deduper/jobs/reportId/<report_id> - Trigger a deduper job for a specific report ID"""
    try:
        # Create new job
        job_id = create_job_id()
        jobs[job_id] = {
            'id': job_id,
            'reportId': report_id,
            'status': JobStatus.PENDING,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'logs': []
        }

        logger.info(f"Created deduper job {job_id} for report ID {report_id}")

        # Start job in background thread with report_id
        thread = threading.Thread(target=run_deduper_job, args=(job_id, report_id))
        thread.daemon = True
        thread.start()

        return jsonify({
            'jobId': job_id,
            'reportId': report_id,
            'status': JobStatus.PENDING
        }), 201

    except Exception as e:
        logger.error(f"Failed to create deduper job for report ID {report_id}: {str(e)}")
        return error_response(
            code='JOB_CREATION_FAILED',
            message=f'Failed to create deduper job for report ID {report_id}',
            status=500,
            details=str(e)
        )

@bp_deduper.route('/deduper/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """GET /deduper/jobs/:id - Fetch job status, timestamps, and logs"""
    if job_id not in jobs:
        return error_response(
            code='JOB_NOT_FOUND',
            message='Job not found',
            status=404
        )

    job = jobs[job_id]
    response = {
        'jobId': job_id,
        'status': job['status'],
        'createdAt': job['created_at']
    }

    if 'reportId' in job:
        response['reportId'] = job['reportId']

    if 'started_at' in job:
        response['startedAt'] = job['started_at']

    if 'completed_at' in job:
        response['completedAt'] = job['completed_at']

    if 'exit_code' in job:
        response['exitCode'] = job['exit_code']

    if 'stdout' in job:
        response['stdout'] = job['stdout']

    if 'stderr' in job:
        response['stderr'] = job['stderr']

    if 'error' in job:
        response['error'] = job['error']


    return jsonify(response)

@bp_deduper.route('/deduper/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """POST /deduper/jobs/:id/cancel - Terminate a running job"""
    if job_id not in jobs:
        logger.warning(f"Attempted to cancel non-existent job {job_id}")
        return error_response(
            code='JOB_NOT_FOUND',
            message='Job not found',
            status=404
        )

    job = jobs[job_id]

    if job['status'] not in [JobStatus.PENDING, JobStatus.RUNNING]:
        logger.warning(f"Cannot cancel job {job_id} with status {job['status']}")
        return error_response(
            code='INVALID_JOB_STATE',
            message=f'Cannot cancel job with status: {job["status"]}',
            status=400
        )

    try:
        # Kill the process if it's running
        if 'process' in job and job['process'].poll() is None:
            job['process'].terminate()
            # Give it a moment, then force kill if needed
            time.sleep(1)
            if job['process'].poll() is None:
                job['process'].kill()

        job['status'] = JobStatus.CANCELLED
        job['completed_at'] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Job {job_id} cancelled successfully")

        return jsonify({
            'jobId': job_id,
            'status': JobStatus.CANCELLED,
            'message': 'Job cancelled successfully'
        })

    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        return error_response(
            code='JOB_CANCELLATION_FAILED',
            message='Failed to cancel job',
            status=500,
            details=str(e)
        )

@bp_deduper.route('/deduper/jobs/list', methods=['GET'])
def get_jobs():
    """GET /deduper/jobs/list - Get all jobs"""
    # Return all jobs (summary)
    all_jobs = []
    for job_id, job_data in jobs.items():
        all_jobs.append({
            'jobId': job_id,
            'status': job_data['status'],
            'createdAt': job_data['created_at']
        })
    return jsonify({'jobs': all_jobs})

@bp_deduper.route('/deduper/health', methods=['GET'])
def health_check():
    """GET /deduper/health - Service health check"""
    try:
        # Check if required environment variables are set
        deduper_path = os.getenv('PATH_TO_MICROSERVICE_DEDUPER')
        python_venv = os.getenv('PATH_TO_PYTHON_VENV')

        checks = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'environment': {
                'deduper_path_configured': bool(deduper_path),
                'python_venv_configured': bool(python_venv)
            },
            'jobs': {
                'total': len(jobs),
                'pending': len([j for j in jobs.values() if j['status'] == JobStatus.PENDING]),
                'running': len([j for j in jobs.values() if j['status'] == JobStatus.RUNNING]),
                'completed': len([j for j in jobs.values() if j['status'] == JobStatus.COMPLETED]),
                'failed': len([j for j in jobs.values() if j['status'] == JobStatus.FAILED]),
                'cancelled': len([j for j in jobs.values() if j['status'] == JobStatus.CANCELLED])
            }
        }

        # Check if deduper path exists
        if deduper_path and not os.path.exists(deduper_path):
            checks['environment']['deduper_path_exists'] = False
            checks['status'] = 'unhealthy'
        elif deduper_path:
            checks['environment']['deduper_path_exists'] = True

        return jsonify(checks)

    except Exception as e:
        logger.exception("Health check failed")
        return error_response(
            code='HEALTH_CHECK_FAILED',
            message='Health check failed',
            status=500,
            details=str(e)
        )

@bp_deduper.route('/deduper/clear-db-table', methods=['DELETE'])
def clear_db_table():
    """DELETE /deduper/clear-db-table - Cancel all jobs and clear the database table"""
    try:
        # Get environment variables
        deduper_path = os.getenv('PATH_TO_MICROSERVICE_DEDUPER')
        python_venv = os.getenv('PATH_TO_PYTHON_VENV')

        if not deduper_path or not python_venv:
            return error_response(
                code='MISSING_CONFIGURATION',
                message='Missing required environment variables',
                status=500,
                details='PATH_TO_MICROSERVICE_DEDUPER and PATH_TO_PYTHON_VENV must be configured'
            )

        # Step 1: Cancel all pending/running jobs
        cancelled_jobs = []
        for job_id, job in jobs.items():
            if job['status'] in [JobStatus.PENDING, JobStatus.RUNNING]:
                try:
                    # Kill the process if it's running
                    if 'process' in job and job['process'].poll() is None:
                        job['process'].terminate()
                        # Give it a moment, then force kill if needed
                        time.sleep(0.5)
                        if job['process'].poll() is None:
                            job['process'].kill()

                    job['status'] = JobStatus.CANCELLED
                    job['completed_at'] = datetime.now(timezone.utc).isoformat()
                    cancelled_jobs.append(job_id)
                except Exception as e:
                    logger.warning(f"[Clear] Failed to cancel job {job_id}: {str(e)}")

        # Step 2: Execute clear_table command immediately (not queued)
        cmd = [
            f"{python_venv}/bin/python",
            f"{deduper_path}/src/main.py",
            "clear_table", "-y"
        ]

        # CRITICAL: Get child process NAME_APP from environment variable
        child_process_name = os.getenv('NAME_CHILD_PROCESS_DEDUPER')
        if not child_process_name:
            raise ValueError("NAME_CHILD_PROCESS_DEDUPER environment variable is required")

        # Inject NAME_APP for child process
        child_env = os.environ.copy()
        child_env['NAME_APP'] = child_process_name

        logger.info(f"[Clear] Executing clear_table command with NAME_APP={child_process_name}: {' '.join(cmd)}")
        logger.info(f"[Clear] Cancelled {len(cancelled_jobs)} jobs: {cancelled_jobs}")

        # Run synchronously and capture output
        result = subprocess.run(
            cmd,
            env=child_env,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout for safety
        )

        # Return response
        response = {
            'cleared': result.returncode == 0,
            'cancelledJobs': cancelled_jobs,
            'exitCode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if result.returncode == 0:
            logger.info(f"[Clear] Successfully cleared database table")
            return jsonify(response), 200
        else:
            logger.error(f"[Clear] Failed to clear database table with exit code {result.returncode}")
            return error_response(
                code='CLEAR_TABLE_FAILED',
                message='Clear table command failed',
                status=500,
                details={
                    'exitCode': result.returncode,
                    'cancelledJobs': cancelled_jobs,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            )

    except subprocess.TimeoutExpired:
        logger.error("[Clear] Clear table command timed out after 60 seconds")
        return error_response(
            code='CLEAR_TABLE_TIMEOUT',
            message='Clear table command timed out after 60 seconds',
            status=500,
            details={'cancelledJobs': cancelled_jobs}
        )
    except Exception as e:
        logger.exception(f"[Clear] Unexpected error during clear table operation: {str(e)}")
        return error_response(
            code='INTERNAL_ERROR',
            message='Unexpected error during clear table operation',
            status=500,
            details={
                'cancelledJobs': cancelled_jobs if 'cancelled_jobs' in locals() else [],
                'error': str(e)
            }
        )