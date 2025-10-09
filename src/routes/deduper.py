from flask import Blueprint, request, jsonify
import subprocess
import threading
import time
import os
from datetime import datetime, timezone

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

def run_deduper_job(job_id):
    """Run the deduper microservice in a separate thread"""
    try:
        jobs[job_id]['status'] = JobStatus.RUNNING
        # jobs[job_id]['started_at'] = datetime.utcnow().isoformat()
        jobs[job_id]['started_at'] = datetime.now(timezone.utc).isoformat()

        # Get deduper path from environment
        deduper_path = os.getenv('PATH_TO_MICROSERVICE_DEDUPER')
        python_venv = os.getenv('PATH_TO_PYTHON_VENV')

        if not deduper_path or not python_venv:
            raise Exception("Missing environment variables for deduper or python venv")

        # Build command to run deduper
        cmd = [
            f"{python_venv}/bin/python",
            f"{deduper_path}/main.py",
            "analyze_fast"  # Default command for deduplication
        ]

        # Note: deduper commands don't take arguments, they process all available data

        # Run the subprocess with output visible in terminal
        print(f"[Job {job_id}] Starting deduper: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            text=True
        )

        jobs[job_id]['process'] = process

        # Wait for completion
        exit_code = process.wait()

        jobs[job_id]['stdout'] = f"Process output streamed to terminal"
        jobs[job_id]['stderr'] = f"Process errors streamed to terminal"
        jobs[job_id]['exit_code'] = process.returncode
        jobs[job_id]['completed_at'] = datetime.now(timezone.utc).isoformat()

        if process.returncode == 0:
            jobs[job_id]['status'] = JobStatus.COMPLETED
        else:
            jobs[job_id]['status'] = JobStatus.FAILED

    except Exception as e:
        jobs[job_id]['status'] = JobStatus.FAILED
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['completed_at'] = datetime.now(timezone.utc).isoformat()

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

        # Start job in background thread
        thread = threading.Thread(target=run_deduper_job, args=(job_id,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'jobId': job_id,
            'status': JobStatus.PENDING
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp_deduper.route('/deduper/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """GET /deduper/jobs/:id - Fetch job status, timestamps, and logs"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    response = {
        'jobId': job_id,
        'status': job['status'],
        'createdAt': job['created_at']
    }

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
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]

    if job['status'] not in [JobStatus.PENDING, JobStatus.RUNNING]:
        return jsonify({
            'error': f'Cannot cancel job with status: {job["status"]}'
        }), 400

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

        return jsonify({
            'jobId': job_id,
            'status': JobStatus.CANCELLED,
            'message': 'Job cancelled successfully'
        })

    except Exception as e:
        return jsonify({'error': f'Failed to cancel job: {str(e)}'}), 500

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
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@bp_deduper.route('/deduper/clear-db-table', methods=['DELETE'])
def clear_db_table():
    """DELETE /deduper/clear-db-table - Cancel all jobs and clear the database table"""
    try:
        # Get environment variables
        deduper_path = os.getenv('PATH_TO_MICROSERVICE_DEDUPER')
        python_venv = os.getenv('PATH_TO_PYTHON_VENV')

        if not deduper_path or not python_venv:
            return jsonify({'error': 'Missing environment variables for deduper or python venv'}), 500

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
                    print(f"[Clear] Warning: Failed to cancel job {job_id}: {str(e)}")

        # Step 2: Execute clear_table command immediately (not queued)
        cmd = [
            f"{python_venv}/bin/python",
            f"{deduper_path}/main.py",
            "clear_table", "-y"
        ]

        print(f"[Clear] Executing clear_table command: {' '.join(cmd)}")
        print(f"[Clear] Cancelled {len(cancelled_jobs)} jobs: {cancelled_jobs}")

        # Run synchronously and capture output
        result = subprocess.run(
            cmd,
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
            return jsonify(response), 200
        else:
            response['error'] = 'Clear table command failed'
            return jsonify(response), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            'error': 'Clear table command timed out',
            'cancelledJobs': cancelled_jobs,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500
    except Exception as e:
        return jsonify({
            'error': str(e),
            'cancelledJobs': cancelled_jobs if 'cancelled_jobs' in locals() else [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500