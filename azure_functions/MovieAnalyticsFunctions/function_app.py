import azure.functions as func
import logging
import json
import subprocess
import sys
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="RunETLJob")
def RunETLJob(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Get job_name from request
    job_name = req.params.get('job_name')
    if not job_name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            job_name = req_body.get('job_name')

    if not job_name:
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": "Please pass a job_name parameter (csv_import, api_refresh, dimensions, fact, aggregations, validation)"
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Map job names to script paths (relative to project root)
    job_scripts = {
        "csv_import": "etl_scripts/etl_csv_to_staging.py",
        "api_refresh": "etl_scripts/etl_api_refresh.py",
        "dimensions": "etl_scripts/etl_load_dimensions.py",
        "fact": "etl_scripts/etl_load_fact.py",
        "aggregations": "etl_scripts/etl_load_aggregations.py",
        "validation": "etl_scripts/etl_data_quality_validation.py"
    }

    if job_name not in job_scripts:
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": f"Unknown job_name: {job_name}. Valid options: {list(job_scripts.keys())}"
            }),
            status_code=400,
            mimetype="application/json"
        )

    script_path = job_scripts[job_name]
    
    # Get absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_script_path = os.path.normpath(os.path.join(current_dir, script_path))

    logging.info(f"Running ETL job: {job_name}")
    logging.info(f"Script path: {full_script_path}")

    try:
        # Check if script exists
        if not os.path.exists(full_script_path):
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": f"Script not found: {full_script_path}"
                }),
                status_code=404,
                mimetype="application/json"
            )

        # Run the Python script
        result = subprocess.run(
            [sys.executable, full_script_path],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        # Prepare response
        response_data = {
            "status": "success" if result.returncode == 0 else "failed",
            "job_name": job_name,
            "returncode": result.returncode,
            "stdout": result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout,  # Last 1000 chars
            "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
        }

        logging.info(f"ETL job {job_name} completed with return code: {result.returncode}")

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200 if result.returncode == 0 else 500,
            mimetype="application/json"
        )

    except subprocess.TimeoutExpired:
        logging.error(f"ETL job {job_name} timed out")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": f"Job {job_name} timed out after 10 minutes"
            }),
            status_code=500,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error running ETL job {job_name}: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )