import boto3
import requests
from datetime import datetime

ec2 = boto3.client('ec2')
s3 = boto3.Session().client('s3')
lab = "lab4"

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

reset_lambda_function_cache(f"test-{lab}")

def get_instances_data(uniid):
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Uniid', 'Values': [uniid]},
            {'Name': 'tag:Lab', 'Values': ['4']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    if len(response['Reservations']) < 3:
        raise Exception(f"\n This lab needs 3 instances to be complete, currently found only {len(response['Reservations'])}.")

    instances = {}
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_data = {}
            instance_type = "db"
            if instance['SubnetId'] == 'subnet-098b2ee2b4fc6d33c':
                instance_type = "mgmt"
            elif 'PublicIpAddress' in instance:
                instance_data["public_ip"] = instance['PublicIpAddress']
                instance_type = "webserver"

            instance_data["id"] = instance['InstanceId']
            instance_data["subnet_id"] = instance['SubnetId']
            instance_data["security_groups"] = instance['SecurityGroups']

            instances[instance_type] = instance_data

    if 'webserver' not in instances:
        raise Exception(f"Didn't find a webpage instance, make sure the webpage instance has a public IPv4")
    return instances

def check_webserver_content(uniid, webserver_public_ip):
    correct_content = "Server version: 5.5.68-MariaDB"
    url = f"http://{webserver_public_ip}"
    try:
        instance_content = requests.get(url, timeout=3)
    except Exception as e:
        raise Exception(f"Your webpage is not accessible {uniid}\nplease check if it opens the public IPv4 on your computer, it it doesn't check the subnet and security groups")

    if correct_content in instance_content.text:
        print(f"The webservers content is correct {uniid}")
    else:
        raise Exception(f"\nThe webserver content is not correct.\nCurrent content is {instance_content.text}but it needs to have {correct_content} in it somewhere")

def check_instances_security_groups(instance_data):
    results = {
        "webserver": {
            'allow_port_80_from_internet': False,
            'allow_port_22_from_mgmt_sg': False
        },
        "db": {
           'allow_port_3306_from_webserver_sg': False,
            'allow_port_22_from_mgmt_sg': False
        }
    }

    mgmt_sg_id = instance_data['mgmt']['security_groups'][0]['GroupId']
    webserver_sg_id = instance_data['webserver']['security_groups'][0]['GroupId']

    for instance_type, data in instance_data.items():
        sg_id = data['security_groups'][0]['GroupId']
        sg_details = ec2.describe_security_groups(GroupIds=[sg_id])
        
        for permission in sg_details['SecurityGroups'][0]['IpPermissions']:
            if permission['FromPort'] == 80 and permission['IpRanges'][0]['CidrIp'] == '0.0.0.0/0':
                results[instance_type]['allow_port_80_from_internet'] = True

            elif permission['FromPort'] == 3306 and permission['UserIdGroupPairs'][0]['GroupId'] == webserver_sg_id:
                results[instance_type]['allow_port_3306_from_webserver_sg'] = True
            
            elif permission['FromPort'] == 22 and instance_type != 'mgmt':
                if permission['UserIdGroupPairs'][0]['GroupId'] == mgmt_sg_id:
                    results[instance_type]['allow_port_22_from_mgmt_sg'] = True

    for instance_type, checks in results.items():
        if not all(checks.values()):
            raise Exception(f"Security group settings for {instance_type} instance failed verification.\n Check results\n{results}")

    print("\nAll of the security groups for the instances have been configured correctly.")

def subnet_has_access_to_internet(type, instance_data):
    subnet_id = instance_data['subnet_id']

    response = ec2.describe_route_tables(Filters=[
        {
            'Name': 'association.subnet-id',
            'Values': [subnet_id]
        }
    ])
    route_tables = response['RouteTables']

    for route_table in route_tables:
        routes = route_table['Routes']
        for route in routes:
            if "igw-" in route['GatewayId']:
                print(f"\nThe {type} subnet {subnet_id} has access to the internet")
                return True
    print(f"The {type} subnet {subnet_id} does NOT have access to the internet")
    return False

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

def lambda_handler(event, context):
    if 'Uniid' not in event:
        raise Exception(f"Event does not contain 'Uniid'.\n The event provided by you is \n{event}\n")

    uniid = event['Uniid']

    if not already_passed(uniid):
        instances_data = get_instances_data(uniid)
        print(instances_data)
        if not subnet_has_access_to_internet(uniid, instances_data['webserver']):
            raise Exception(f"webserver can't access the internet")
        if subnet_has_access_to_internet("webserver", instances_data['db']):
            raise Exception(f"The db should not have access to the internet, the subnet is wrongly configured")
        check_webserver_content("db", instances_data['webserver']['public_ip'])
        check_instances_security_groups(instances_data)
        pass_student(uniid)


#lambda_handler({"Uniid": "lars"}, "test")