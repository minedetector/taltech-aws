import json
import boto3
import requests

s3 = boto3.client('s3')
ec2 = boto3.client('ec2')

lab = "lab6"

# Set the bucket name
bucket_name = 'ica0017-lab6-states'

def check_security_group_ingress(ingress_rules):
    ssh_allowed = False
    http_allowed = False
    for rule in ingress_rules:
        if rule['from_port'] == 22:
            ssh_allowed = True
        elif rule['from_port'] == 80:
            http_allowed = True
    if ssh_allowed and http_allowed:
        return True
    return False

def get_current_public_ip(instance_id):
    instance_public_ip = ec2.describe_instances(Filters=[
        {
            'Name': 'instance-id',
            'Values': [instance_id]
        }
    ])["Reservations"][0]["Instances"][0]["PublicIpAddress"]
    return instance_public_ip

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
        print(f'passed.txt has been uploaded to {lab}/{uni_id}/passed.txt\n')
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
    # List all objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name)

    # Loop through each object in the response
    for obj in response['Contents']:
        # Get the object key (i.e., file path)
        obj_key = obj['Key']
        
        # Get the object content
        obj_response = s3.get_object(Bucket=bucket_name, Key=obj_key)
        
        # Read the object content as a string
        obj_content = obj_response['Body'].read().decode('utf-8')
        
        website, uni_id = None, None

        try:
            obj_json = json.loads(obj_content)
            for resource in obj_json["resources"]:
                if resource["type"] == "aws_instance":
                    try:
                        uni_id = resource["instances"][0]["attributes"]["tags"]["User"]
                    except:
                        print("Instance has no User tag defined.")
                        continue
                    instance_id = resource["instances"][0]["attributes"]["id"]
                    website = get_current_public_ip(instance_id)
                    if not website:
                        print("There is no public IP defined for the instance, please check subnet")
                        continue
                elif resource["type"] == "aws_security_group":
                    ingress_rules = resource["instances"][0]["attributes"]["ingress"]
            if check_security_group_ingress(ingress_rules):
                student = None
                try:
                    student = event['User']
                except:
                    pass
                if student and uni_id != student:
                    continue
                elif already_passed(uni_id):
                    continue
                try:
                    website_content = requests.get(f"http://{website}", timeout=3)
                    if uni_id in website_content.text:
                        create_passed_file(uni_id)
                    else:
                        print(f"The website has no mention of {uni_id}, content of the website is {website_content.text}")
                        continue
                except:
                    print("Website not reachable, make sure the instances are still running, http is allowed and the connected subnet is publid and has internet access.")
        except json.JSONDecodeError:
            # If it's not a JSON object, ignore it
            pass