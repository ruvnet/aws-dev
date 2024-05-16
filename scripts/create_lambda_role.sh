#!/bin/bash

# Define variables
ROLE_NAME="hello-word-2"

# Create the trust policy JSON file
cat <<EOT > trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOT

# Create the IAM role
aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://trust-policy.json

# Attach the AWSLambdaBasicExecutionRole policy to the role
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

echo "IAM role '$ROLE_NAME' created and policy attached successfully."
