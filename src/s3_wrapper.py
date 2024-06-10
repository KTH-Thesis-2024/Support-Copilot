import json
from typing import Any, Dict

import boto3  # type: ignore

from src import logger


def retrieve_s3_payload(s3_payload_path: str) -> Dict[str, Any]:
    try:
        payload_path_parts = s3_payload_path.split("/")
        bucket_name = payload_path_parts[1]
        file_location = "/".join(payload_path_parts[2:])

        s3_boto3_client: boto3.client = boto3.client("s3")

        s3_object: Dict[str, Any] = s3_boto3_client.get_object(
                Bucket=bucket_name,
                Key=file_location
        )

        s3_payload: Dict[str, Any] = json.loads(
                s3_object["Body"].read().decode("utf-8"))

        logger.info("S3 payload retrieved and decoded successfully.")
        return s3_payload

    except IndexError:
        logger.error("Invalid S3 payload path.")
        raise ValueError("Invalid S3 payload path.")

    except ValueError:
        logger.error("Failed to decode S3 payload.")
        raise RuntimeError("Failed to decode S3 payload.")

    except Exception as error:
        logger.error(f"Failed to retrieve S3 payload: {str(error)}")
        raise RuntimeError(f"Failed to retrieve S3 payload: {str(error)}")
