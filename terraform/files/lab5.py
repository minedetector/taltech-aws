import boto3
import requests
from datetime import datetime

ec2 = boto3.client('ec2')
elbv2 = boto3.client('elbv2')
s3 = boto3.Session().client('s3')
autoscaling = boto3.client('autoscaling')
lab = "lab5"

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

def get_asg_data(uniid):
    asg = autoscaling.describe_auto_scaling_groups(
        Filters=[
            {
                'Name': 'tag:Uniid',
                'Values': [uniid]
            }
        ]
    )
    
    if not asg['AutoScalingGroups']:
        raise Exception(f"There doesn't exist a ASG where the Uniid tag equals to {uniid}")
    
    asg = asg['AutoScalingGroups'][0]
    asg_info = {}

    asg_info["launch_template_id"] = asg["LaunchTemplate"]["LaunchTemplateId"]
    asg_info["asg_subnets"] = asg['VPCZoneIdentifier']

    print(f"Found your ASG {uniid}")

    return asg_info

def get_sg_from_lt(asg_data):
    try:
        lt = ec2.describe_launch_template_versions(
            LaunchTemplateId=asg_data["launch_template_id"]
        )['LaunchTemplateVersions'][0]['LaunchTemplateData']['SecurityGroupIds'][0]

        print("Found the Security Group that is attached to the launch template")

        return lt
    except:
        raise Exception(f"\nLaunch template doesn't have a security group attached to it")
    
def check_webservers_security_group(sg_id):

    sg = ec2.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]
    ingress_rules = sg['IpPermissions']

    webserver = {
        'allow_port_80_from_internet': False,
        'allow_port_22_from_mgmt_sg': False
    }

    for rule in ingress_rules:
        if rule['FromPort'] == 80 and rule['IpRanges'][0]['CidrIp'] == '0.0.0.0/0':
                webserver['allow_port_80_from_internet'] = True
        
        if rule['FromPort'] == 22 and len(rule['UserIdGroupPairs']) > 0:
            webserver['allow_port_22_from_mgmt_sg'] = True

    if not all(webserver.values()):
        raise Exception(f"Security group {sg_id} failed verification.\n Check results\n{webserver}")

    print("All of the security groups for the instances have been configured correctly.")

def get_lb_dns_name(uniid):
    load_balancers = elbv2.describe_load_balancers()['LoadBalancers']
    alb_arns = [lb['LoadBalancerArn'] for lb in load_balancers if lb['Type'] == 'application']

    if alb_arns:
        tag_descriptions = elbv2.describe_tags(ResourceArns=alb_arns)['TagDescriptions']
        filtered_albs_arns = [
            tag_desc['ResourceArn'] for tag_desc in tag_descriptions
            if any(tag['Key'] == 'Uniid' and tag['Value'] == uniid for tag in tag_desc['Tags'])
        ]

        if filtered_albs_arns==[]:
            raise Exception(f"Didn't find a ALB with the tag Uniid = {uniid}, please add it to your ALB.")

        matched_alb_dns_names = [
            lb['DNSName'] for lb in load_balancers if lb['LoadBalancerArn'] in filtered_albs_arns
        ]
        print("Found the DNS Name for your ALB.")
        return matched_alb_dns_names[0]

def check_webserver_content(dns_name):
    different_websites = set()

    for i in range (1, 5, 1):
        website_content = requests.get(f"http://{dns_name}", timeout=3)
        different_websites.add(website_content.text)
    if len(different_websites) <= 1:
        raise Exception(f"The website content didn't differ, make sure that you have multiple instances running.\nGot this content only {different_websites}")
    print("Website content check passed, content is different on refreshes")

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
        asg_data = get_asg_data(uniid)
        sg_id = get_sg_from_lt(asg_data)
        check_webservers_security_group(sg_id)
        dns_name = get_lb_dns_name(uniid)
        check_webserver_content(dns_name)
        pass_student(uniid)

#lambda_handler({"Uniid": "lars"}, "test")