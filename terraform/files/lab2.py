import boto3
import subprocess
import json
import requests
from datetime import datetime

# This is dumb
# But for some reason this lambda function decides to cache the results of the previous run
# meaning it doesn't show the correct output when students change something.
# How big is the cache ? Does it have a TTL ? Who knows, thanks AWS
def reset_lambda_function_cache(function_name):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    lambda_client = boto3.client('lambda')
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        Description=current_time
    )

reset_lambda_function_cache("test-lab2")

ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
s3 = boto3.Session().client('s3')

lab = "lab2"

def already_passed(uniid):
    try:
        s3.head_object(Bucket='ica0017-results', Key=f'{lab}/{uniid}/')
        print(f'Congrats {uniid}, you have already passed {lab}')
        return True
    except:
        return False

def get_students_instance(uniid):
    filters = [
        {
            'Name': 'tag:Uniid',
            'Values': [uniid]
        },
        {
            'Name': 'tag:Lab',
            'Values': ["2"]
        },
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ]

    instances = list(ec2.instances.filter(Filters=filters))

    if not instances:
        raise Exception(f"Didn't find a running instance with the tags Uniid={uniid} and Lab=2.")

    if len(instances) > 1:
        raise Exception(f"Found {len(instances)} that use the same uniid, this test requires only 1 instance. \nPlease delete the extra node")
    
    print("Found the instance with the following configuration")
    print(f'Instance ID: {instances[0].id}')
    print(f'Public IP Address: {instances[0].public_ip_address}')

    return instances[0]
    
def check_webserver_content(uniid, student_instance):
    url = f"http://{student_instance.public_ip_address}"
    try:
        instance_content = requests.get(url, timeout=3)
    except Exception as e:
        raise Exception(f"Your webpage is not accessible {uniid}\nplease check if it opens the public IPv4 on your computer, it it doesn't check the subnet and security groups")

    if uniid in instance_content.text:
        print(f"The webservers content is correct {uniid}")

def check_attached_security_group(uniid, student_instance):
    security_groups = student_instance.security_groups
    allowed_ports = {22, 80}
    found_ports = set()

    for sg in security_groups:
        sg_id = sg['GroupId']

        security_group_details = ec2_client.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]

        for permission in security_group_details['IpPermissions']:
            if permission['FromPort'] <= 80 <= permission['ToPort']:
                found_ports.append(80)
            if permission['FromPort'] <= 22 <= permission['ToPort']:
                found_ports.append(22)
        
        if found_ports == allowed_ports:
            print("Security Group correctly configured.")
        else:
            raise Exception(f"  Incorrect configuration: Ports {found_ports} are open. Expected only 22 and 80.")

def pass_student(uniid):
    try:
        s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{uniid}/")
        print(f"{uniid} folder created in the ica0017-results bucket")
        print(f"Congratiulations {uniid}, you have passed {lab}")
    except Exception as e:
        raise Exception(f"Error creating {uniid} folder in the ica0017-results bucket: {e}\nContact the teacher")

def lambda_handler(event, context=""):
    if 'Uniid' not in event:
        print("Event does not contain 'Uniid'.")
        print(f"Event body: \n{event}\n")
        return {
            'statusCode': 404,
            'body': json.dumps({'error': "Missing 'Uniid' in event"})
        }
    
    uniid = event['Uniid']
    if not already_passed(uniid):
        student_instance = get_students_instance(uniid)
        check_attached_security_group(uniid, student_instance)
        check_webserver_content(uniid, student_instance)
        pass_student(uniid)
    return {
        'statusCode': 200,
        'body': {'message': f'{lab} completed!'}
    }

#lambda_handler({"Uniid": "lars"})