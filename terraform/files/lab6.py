import json
import boto3
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

reset_lambda_function_cache("test-lab6")

s3 = boto3.client('s3')
ec2 = boto3.client('ec2')

lab = "lab6"

# Set the bucket name
bucket_name = 'ica0017-lab6-states'

def get_student_tf_state_file(uniid):
    files = s3.list_objects_v2(Bucket=bucket_name)
    for file in files['Contents']:
        if uniid in file['Key']:
            return file['Key']
    raise Exception(f"Didn't find any terraform state files that have {uniid} in their name")

def check_all_required_resources_exist(tf_resource_map):
    expected_resources = {'aws_instance', 'aws_security_group'}
    found_types = {item['type'] for item in tf_resource_map.values()}

    if not expected_resources.issubset(found_types):
        missing_types = expected_resources - found_types
        raise Exception(f"\nMissing required types: {', '.join(missing_types)}")
    print(f"Found the AWS instance and security group in terraform state")

def check_security_group_ingress(sg_data):
    ingress_rules = sg_data["instances"][0]["attributes"]["ingress"] 

    required_ports = {22, 80}
    from_ports = {rule['from_port'] for rule in ingress_rules}

    if required_ports.issubset(from_ports):
        print("SSH and HTTP rules for the security group are configured correctly")
    else:
        missing_ports = required_ports - from_ports
        raise Exception(f"Missing required ports: {', '.join(map(str, missing_ports))}")

def get_instance_public_ip(tf_resource_map):
    instance_id = tf_resource_map['aws_instance']["instances"][0]["attributes"]["id"]
    
    instance = ec2.describe_instances(Filters=[
        {'Name': 'instance-id', 'Values': [instance_id]},
        {'Name': 'instance-state-code', 'Values': ['16']}
    ])

    if instance["Reservations"] == []:
        raise Exception(f"{instance_id} is not running at the moment, can't finish test")
    
    if "PublicIpAddress" in instance["Reservations"][0]["Instances"][0]:
        public_ip = instance["Reservations"][0]["Instances"][0]["PublicIpAddress"]
        print(f"Found the public IP of the instance: {public_ip}")
        return public_ip
    raise Exception(f"There isn't a public IP defined for the instance {instance_id}.")

def check_website_content_is_correct(uniid, website_url):
    try:
        website_content = requests.get(f"http://{website_url}", timeout=3)
        if uniid in website_content.text:
            print(f"Website has the Uni-id {uniid} in it")
        else:
            raise Exception(f"The website has no mention of {uniid}, content of the website is {website_content.text}")
    except:
        raise Exception("Website not reachable, make sure the instances are still running, http is allowed and the connected subnet is publid and has internet access.")

def pass_student(uniid):
    try:
        s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{uniid}/")
        print(f"{uniid} folder created in the ica0017-results bucket")
        print(f"Congratiulations {uniid}, you have passed lab  {lab}")
    except Exception as e:
        raise Exception(f"Error creating {uniid} folder in the ica0017-results bucket: {e}\nContact the teacher")

def already_passed(uniid):
    try:
        s3.head_object(Bucket='ica0017-results', Key=f'{lab}/{uniid}/')
        print(f'Congrats {uniid}, you have already passed lab {lab}')
        return True
    except:
        return False

def lambda_handler(event, text):
    if 'Uniid' not in event:
        raise Exception(f"Event does not contain 'Uniid'.\n The event provided by you is \n{event}\n")

    uniid = event['Uniid']

    if not already_passed(uniid):
        tf_state_file = get_student_tf_state_file(uniid)
        tf_state_content = s3.get_object(Bucket=bucket_name, Key=tf_state_file)['Body'].read().decode('utf-8')

        obj_json = json.loads(tf_state_content)
        tf_resource_map = {resource["type"]: resource for resource in obj_json["resources"]}

        check_all_required_resources_exist(tf_resource_map)
        check_security_group_ingress(tf_resource_map['aws_security_group'])
        website_url = get_instance_public_ip(tf_resource_map) 

        check_website_content_is_correct(uniid, website_url)
        pass_student(uniid)
 
#lambda_handler({"Uniid": "salli"}, "test")