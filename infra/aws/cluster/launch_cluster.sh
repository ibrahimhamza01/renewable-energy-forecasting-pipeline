#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

COUNT=${1:-2}

AMI="ami-0ec10929233384c7f"
INSTANCE_TYPE="t3.large"
KEY_NAME="syed-datsbd-s2026"
SECURITY_GROUP="sg-042c6bd7942058045"
SUBNET="subnet-0bcd46ef182efa9bf"
IAM_ROLE="LabInstanceProfile"

echo "Launching $COUNT worker EC2 instances..."

aws ec2 run-instances \
  --image-id "$AMI" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SECURITY_GROUP" \
  --subnet-id "$SUBNET" \
  --iam-instance-profile Name="$IAM_ROLE" \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
  --count "$COUNT" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=spark-worker}]' \
  --query 'Instances[*].InstanceId' \
  --output text > "${SCRIPT_DIR}/worker_ids.txt"

echo "Waiting for instances to be running..."
sleep 20

echo "Fetching worker IPs..."

aws ec2 describe-instances \
  --instance-ids $(cat "${SCRIPT_DIR}/worker_ids.txt") \
  --query "Reservations[*].Instances[*].PublicIpAddress" \
  --output text | tr ' \t' '\n' | grep -v '^$' > "${SCRIPT_DIR}/workers.txt"

echo "Workers launched:"
cat "${SCRIPT_DIR}/workers.txt"