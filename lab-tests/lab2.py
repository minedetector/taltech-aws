import boto3
import subprocess
import json
import requests
from datetime import datetime

now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)

lambda_client = boto3.client('lambda')

# This is dumb
# But for some reason this lambda function decides to cache the results of the previous run
# meaning it doesn't show the correct output when students change something.
# How big is the cache ? Does it have a TTL ? Who knows, thanks AWS
def reset_lambda_function_cache(function_name):
    response = lambda_client.update_function_configuration(
        FunctionName=function_name,
        Description=current_time
    )
    print(f"Lambda function {function_name} updated successfully.")

reset_lambda_function_cache("test-lab2")

# Create a session using the default profile
session = boto3.Session()

# Create a client to interact with the EC2 service
ec2 = session.client('ec2')

# Create a client to interact with the S3 service
s3 = session.client('s3')

# Use the describe_instances method to retrieve information about all instances
instances = ec2.describe_instances()

# Get all security groups
security_groups = ec2.describe_security_groups()['SecurityGroups']

# Create a list to store the instances' Name tags and public IP addresses
instances_data = []

lab = "lab2"


def already_passed(name):
    # Check if the passed.txt file exists in the folder
    try:
        s3.head_object(Bucket='ica0017-results', Key=f'{lab}/{name}/passed.txt')
        print(f'passed.txt exists in the {lab}/{name}/ folder')
        # Get the tags of the file
        tags = s3.get_object_tagging(Bucket='ica0017-results', Key=f'{lab}/{name}/passed.txt')['TagSet']
        passed = False
        author = False
        #iterate through the tags and check if the passed and author tags are correct
        for tag in tags:
            if tag['Key'] == 'passed' and tag['Value'] == 'true':
                passed = True
            if tag['Key'] == 'author' and tag['Value'] == 'lambda':
                author = True
        if passed and author:
            print('passed.txt has the correct tags')
            return True
        else:
            print('passed.txt does not have the correct tags')
    except:
        print(f'passed.txt does not exist in the {lab}/{name}/ folder')
    return False

def get_instances_tags_ip():
    # Iterate through the reservations and instances to extract the data
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] != "running":
                continue
            name_tag = None
            try:
                public_ip = instance['PublicIpAddress']
            except:
                pass


            # Check if the instance has a Name tag
            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    name_tag = tag['Value']
                    break

            # Append the instance's Name tag and public IP address to the list
            instances_data.append({'Name': name_tag, 'Public IP': public_ip})

def check_security_groups(sg_name):
    # Loop through all security groups
    for security_group in security_groups:
        # Get the tags for the current security group
        tags = security_group.get('Tags', [])
        tag_set = False
        
        # Check if the tag with the key 'Name' and value UNI-id exists
        for tag in tags:
            if tag['Key'] == 'Name' and tag['Value'] == sg_name:
                tag_set = True
                print(f"Security Group {sg_name} with id {security_group['GroupId']} has the desired tag")

                inbound_rules = security_group['IpPermissions']

                # Check if the security group only allows inbound connections from SSH and HTTP
                ssh_allowed = False
                http_allowed = False
                for rule in inbound_rules:
                    for ip_range in rule.get('IpRanges', []):
                        try:
                            if rule['FromPort'] == 22:
                                ssh_allowed = True
                            elif rule['FromPort'] == 80:
                                http_allowed = True
                        except:
                            print(f"No spcific port ranges in security group {sg_name}")
                        if ssh_allowed and http_allowed:
                            break

                    if ssh_allowed and http_allowed:
                        break
                
                if ssh_allowed and http_allowed:
                    print(f"Security Group {sg_name} with id {security_group['GroupId']} has allowed inbound connections from SSH and HTTP")
                    return True
                else:
                    print(f"Security Group {sg_name} with id {security_group['GroupId']} does not have allowed inbound connections from SSH and HTTP")
    if tag_set == False:
        print(f"No SG-s with the tag Name={sg_name}")
    return False

def check_instances(event):
    # Iterate through the instances_data and curl the public IP address
    uni_id = None
    try:
        uni_id = event['Name']
    except:
        pass
    for instance in instances_data:
        name = instance['Name']
        if uni_id != None and uni_id not in name:
            continue
        public_ip = instance['Public IP']

        # Use requests to get the contents of the instance
        result = requests.get(f"http://{public_ip}")

        if already_passed(name):
            print(f"{name} already exists and passed")
            continue

        # Compare the webpage contents with the Name tag
        if name in result.text and check_security_groups(name):
            print(f"Instance {name} has the correct Name tag")
            #create a folder in the ica0017-results bucket
            try:
                s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{name}/")
                print(f"{name} folder created in the ica0017-results bucket")
                # Create a list of tags
                tags = [{'Key': 'passed', 'Value': 'true'}, {'Key': 'author', 'Value': 'lambda'}]

                # Create passed.txt file
                # subprocess.run(["touch", "passed.txt"])

                # Upload the file to S3
                s3.upload_file("passed.txt", 'ica0017-results', f'{lab}/{name}/passed.txt')

                # Add tags to the uploaded file
                s3.put_object_tagging(Bucket='ica0017-results', Key=f'{lab}/{name}/passed.txt', Tagging={'TagSet': tags})
                print(f'passed.txt has been uploaded to {lab}/{name} with tags')
            except Exception as e:
                print(f"Error creating {name} folder in the ica0017-results bucket: {e}")
        else:
            print(f"Instance {name} does not have the correct Name tag")

def lambda_handler(event, context):
    get_instances_tags_ip()
    check_instances(event)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'Hello, DONE!'})
    }

#lambda_handler("test", "test")
