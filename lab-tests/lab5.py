import boto3
import requests

# create an EC2 client
elbv2 = boto3.client('elbv2')
ec2 = boto3.client('ec2')
autoscaling = boto3.client('autoscaling')
s3 = boto3.client('s3')

lab = "lab5"

def get_target_group_data():
    # get a list of all target groups
    target_groups = elbv2.describe_target_groups()['TargetGroups']

    vpc_id = "vpc-05c91d040c3aa10ff"

    user_values = []
    tg_data = {}

    # loop through each target group and extract the "User" tag value
    for tg in target_groups:
        # get the tags for the target group
        tags_response = elbv2.describe_tags(ResourceArns=[tg['TargetGroupArn']])
        for tag in tags_response['TagDescriptions'][0]['Tags']:
            # check if the tag key is "User"
            if tag['Key'] == 'User':
                uni_id = tag['Value']
                if tg['Port'] != 80 or tg['VpcId'] != vpc_id or tg['ProtocolVersion'] != 'HTTP1':
                    print(f"""
                        Something isn't configured properly
                        Port should be 80, current value is {tg['Port']}
                        VPC Id should be {vpc_id}, current value is {tg['VpcId']}
                        ProtocolVersion should be HTTP1, current value is {tg['ProtocolVersion']}
                    """)
                    continue
                user_values.append(uni_id)
                tg_data[uni_id] = {
                    "lb_id": tg["LoadBalancerArns"][0], 
                    "tg_arn": tg["TargetGroupArn"]
                    }
    return tg_data

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
                print(f"\nThe {type} subnet {subnet_id} of {uni_id} has access to the internet")
                return True
    print(f"\nThe {type} subnet {subnet_id} of {uni_id} does NOT have access to the internet")
    return False

def get_lb_address(uni_id, data):
    load_balancers = elbv2.describe_load_balancers()

    for lb in load_balancers['LoadBalancers']:
        correct_tg = False
        # check if the type is application load balancer
        if lb['Type'] != 'application':
            print("The type of the Load balancer is wrong, should be application.")
            continue
        tags_response = elbv2.describe_tags(ResourceArns=[lb['LoadBalancerArn']])
        for tag in tags_response['TagDescriptions'][0]['Tags']:
            # check if the loadbalancer has the same User tag as does one of the target groups
            if tag['Key'] == 'User' and tag['Value'] == uni_id:
                # Check if the Loadbalancer attached to the Target Group is correct
                if data["lb_id"] == lb["LoadBalancerArn"]:
                    correct_tg = True
                else:
                    print(f"The Target Group with the tag User: {uni_id} is attached to the wrong Load balancer.")
                    return False
                if correct_tg:
                    subnets = lb['AvailabilityZones']
                    for subnet in subnets:
                        if not check_subnet_internet_access("public", uni_id, subnet["SubnetId"]):
                            print(f"The subnet {subnet} does not have internet access.")
                            return False
                else:
                    print(f"The User tag on the Loadbalancer: {tag['Value']} does not match any of the tags on the target groups")
        return lb["DNSName"]

def check_security_groups(uni_id, sg_id):
    # Get all security groups
    security_group = ec2.describe_security_groups(Filters=[
        {
            'Name': 'group-id',
            'Values': [sg_id]
        }
        ]
    )['SecurityGroups'][0]

    tags = security_group['Tags']
    tag_set = False
    
    # Check if the tag with the key 'Name' and value UNI-id exists
    for tag in tags:
        if tag['Key'] == 'Name' and uni_id in tag['Value']:
            tag_set = True
            print(f"Security Group of student {uni_id} with id {sg_id} has the desired tag")

            inbound_rules = security_group['IpPermissions']

            # Check if the security group only allows inbound connections from SSH and HTTP
            ssh_allowed = False
            http_allowed = False
            for rule in inbound_rules:
                try:
                    if rule['FromPort'] == 22 and len(rule['UserIdGroupPairs']) > 0:
                        ssh_allowed = True
                    elif rule['FromPort'] == 80:
                        http_allowed = True
                except:
                    print(f"No spcific port ranges in security group {sg_id}")

                if ssh_allowed and http_allowed:
                    break
            
            if ssh_allowed and http_allowed:
                print(f"Security Group {uni_id} with id {sg_id} has allowed inbound connections from SSH and HTTP")
                return True
            else:
                print(f"Security Group {uni_id} with id {sg_id} does not have correct HTTP and SSH set up, make sure that port 80 is allowed for inbound and that SSH is allowed from other security group")
    if tag_set == False:
        print(f"No SG-s for student {uni_id}")
    return False

def get_launch_configuration_name(uni_id):
    # Get the launch configuration name
    response = autoscaling.describe_launch_configurations()['LaunchConfigurations']
    for lc in response:
        if uni_id in lc['LaunchConfigurationName']:
            sg_id = lc['SecurityGroups'][0]
            if check_security_groups(uni_id, sg_id):
                return lc['LaunchConfigurationName']
        else:
            print(f"didn't find a launch configuration that has {uni_id} in name")
    return None

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
                print(f"\nThe {type} subnet {subnet_id} of {uni_id} has access to the internet")
                return True
    print(f"\nThe {type} subnet {subnet_id} of {uni_id} does NOT have access to the internet")
    return False

def correct_autoscaling_group(uni_id, lc_name, tg_arn):
    asg = autoscaling.describe_auto_scaling_groups(
        Filters=[
            {
                'Name': 'tag:User',
                'Values': [uni_id]
            }
        ]
    )['AutoScalingGroups'][0]
    if asg['LaunchConfigurationName'] != lc_name:
        print(f"Autoscaling group for {uni_id} does not use the correct launch configuration, should use {lc_name}, but is using {asg['LaunchConfigurationName']}")
        return False
    subnets = asg["VPCZoneIdentifier"].split(",")
    for subnet in subnets:
        if not check_subnet_internet_access("public", uni_id, subnet):
            return False
    if tg_arn not in asg['TargetGroupARNs']:
        print(f"""
        Wrong target group attached to autoscaling group.
        Target group attached to autoscaling group is {asg['TargetGroupARNs'][0]}
        but should be {tg_arn} instead 
        """)
        return False
    return True

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

def lambda_handler(event, text):
    target_group_data = get_target_group_data()
    for uni_id, data in target_group_data.items():
        student = None
        try:
            student = event['User']
        except:
            pass
        if student != None and uni_id != student:
            continue
        if already_passed(uni_id):
            print(f"{uni_id} already passed")
            continue
        website_address = get_lb_address(uni_id, data)
        if not website_address:
            lb_id = data["lb_id"]
            print(f"Load balancer {lb_id} for student {uni_id} is not correct")
            continue
        lc_name = get_launch_configuration_name(uni_id)
        if not lc_name:
            continue
        if not correct_autoscaling_group(uni_id, lc_name, data["tg_arn"]):
            continue
        different_websites = set()

        for i in range (5):
            website_content = requests.get(f"http://{website_address}", timeout=3)
            different_websites.add(website_content.text)
        
        if len(different_websites) > 1:
            create_passed_file(uni_id)
            
lambda_handler("test", "tests")
