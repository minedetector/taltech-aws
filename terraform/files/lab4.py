import boto3
import requests
import json
from datetime import datetime

ec2 = boto3.client('ec2')
s3 = boto3.client('s3')

lab = "lab4"

now = datetime.now()

current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)

lambda_client = boto3.client('lambda')

def reset_lambda_function_cache(function_name):
    response = lambda_client.update_function_configuration(
        FunctionName=function_name,
        Description=current_time
    )
    print(f"Lambda function {function_name} updated successfully.")

reset_lambda_function_cache("test-lab4")

def get_public_subnets():
    response = ec2.describe_subnets(Filters=[
        {
            'Name': 'mapPublicIpOnLaunch',
            'Values': ['true']
        },
        {
            'Name': 'tag:User',
            'Values': ['*']
        }
    ])

    return response['Subnets']

def check_subnet_internet_access(type, uni_id, subnet_id):
    # Retrieve the route table associated with the subnet
    response = ec2.describe_route_tables(Filters=[
        {
            'Name': 'association.subnet-id',
            'Values': [subnet_id]
        }
    ])
    route_tables = response['RouteTables']

    # Check if the route table has a route to an internet gateway
    for route_table in route_tables:
        routes = route_table['Routes']
        for route in routes:
            if "igw-" in route['GatewayId']:
                print(" ")
                print(f"The {type} subnet {subnet_id} of {uni_id} has access to the internet")
                return True
    print(f"The {type} subnet {subnet_id} of {uni_id} does NOT have access to the internet")
    return False

def get_private_subnet_id(uni_id):
    response = ec2.describe_subnets(Filters=[
        {
            'Name': 'mapPublicIpOnLaunch',
            'Values': ['false']
        },
        {
            'Name': 'tag:Name',
            'Values': [f"{uni_id}*"]
        }
    ])
    if len(response["Subnets"]) == 0:
        print(f"No private subnet found for {uni_id}, please check that it exists and has the Name tag assigned")
        return None
    else:
        print(f"\nPrivate subnet exists for {uni_id}")
        return response["Subnets"][0]["SubnetId"]

def get_instance_in_subnet(uni_id, subnet_id):
    instance_id = None
    response = ec2.describe_instances(Filters=[
        {
            'Name': 'subnet-id',
            'Values': [subnet_id]
        },
        {
            'Name': 'tag:Name',
            'Values': [f"{uni_id}*"]
        }
    ])
    if (len(response["Reservations"]) >= 1):
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                if 'Tags' in instance:
                    name_tags = [tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'Name']
                    if not any('temp' in name_tag.lower() for name_tag in name_tags):
                        instance_id = instance["InstanceId"]
    return instance_id

def get_instance_public_ip(instance_id):
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'instance-id',
                'Values': [instance_id]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ],
        InstanceIds=[instance_id]
    )
    if len(response["Reservations"]) == 0 or "PublicIpAddress" not in response["Reservations"][0]["Instances"][0]:
        return None
    return response["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    
def check_public_instance_contents(public_ip):
    correct_texts = ["Server version: 5.5.68-MariaDB", "Connect failed: Access denied for user"]
    try:
        print(f"Trying to get the contents of the public IP: {public_ip}")
        result = requests.get(f"http://{public_ip}", timeout=3)
    except:
        print("Website content is not availalbe, please check the public IP manually and see if the subnet and security group are correct.")
        return False

    return any(text in result.text for text in correct_texts)

def create_passed_file(uni_id):
    try:
        s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{uni_id}/")
        print(f"{uni_id} folder created in the ica0017-results bucket")
        # Create a list of tags
        tags = [{'Key': 'passed', 'Value': 'true'}, {'Key': 'author', 'Value': 'lambda'}]

        # Upload the file to S3
        s3.upload_file("passed.txt", 'ica0017-results', f'{lab}/{uni_id}/passed.txt')

        # Add tags to the uploaded file
        s3.put_object_tagging(Bucket='ica0017-results', Key=f'{lab}/{uni_id}/passed.txt', Tagging={'TagSet': tags})
        print(f'passed.txt has been uploaded to {lab}/{uni_id}/passed.txt with tags')
    except Exception as e:
        print(f"Error creating {uni_id} folder in the ica0017-results bucket: {e}")

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

def lambda_handler(event, context):
    subnets = get_public_subnets()

    for subnet in subnets:
        # Check if the subnet has a tag named 'Name'
        if 'Tags' in subnet:
            for tag in subnet['Tags']:
                if tag['Key'] == 'User':
                    # Check if the subnet has internet access
                    uni_id = tag['Value']
                    student = None

                    try:
                        student = event['User']
                    except:
                        pass
                    
                    if student != None and uni_id != student:
                        continue
                    elif already_passed(uni_id):
                        print(f"{uni_id} already passed")
                        continue

                    public_subnet_id = subnet['SubnetId']
                    if not check_subnet_internet_access("public", uni_id, public_subnet_id):
                        continue
                    private_subnet_id = get_private_subnet_id(uni_id)
                    if not private_subnet_id:
                        continue
                    if check_subnet_internet_access("private", uni_id, private_subnet_id):
                        continue
                    public_instance_id = get_instance_in_subnet(uni_id, public_subnet_id)
                    if not public_instance_id:
                        print(f"No instances found in the public subnet: {public_subnet_id}")
                        print("Make sure the instance is running and has a User tag defined.")
                        continue
                    public_instance_public_ip = get_instance_public_ip(public_instance_id)
                    if public_instance_public_ip:
                        if check_public_instance_contents(public_instance_public_ip):
                            print("Website content is correct")
                        else:
                            print("""
                                    Website content is not correct.
                                    Does the website show either a
                                    - server version
                                    - failed to connect message
                                    if neither are shown then lab is not passed.
                                    Check the website and try to figure out the issue.
                                """)
                            continue
                    else:
                        print(" ")
                        print(f"Instance {public_instance_id} has no public IP currently.")
                        print(f"Check if the instance is running {uni_id}")
                        continue
                    private_instance_id = get_instance_in_subnet(uni_id, private_subnet_id)
                    if not get_instance_public_ip(private_instance_id):
                        print("Private instance has no public IP attached, which is correct.")
                    create_passed_file(uni_id)
    return {
        'statusCode': 200,
        'body': json.dumps('Successful')
    }

#lambda_handler({"User": "larasi"}, "test")