import boto3
import urllib.request
import json
import subprocess

# Initialize the s3 client
s3 = boto3.client('s3')

lab = "lab3"

# Get a list of all buckets with the prefix ica0017
response = s3.list_buckets()
buckets = [bucket['Name'] for bucket in response['Buckets'] if bucket['Name'].startswith('ica0017') and bucket['Name'] != "ica0017-results"]

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
    # Iterate over the buckets and check if they have public site hosting enabled
    for bucket in buckets:
        uni_id = None
        try:
            uni_id = event['Name']
        except:
            pass
        if uni_id != None and uni_id not in bucket:
            continue
        try:
            response = s3.get_bucket_website(Bucket=bucket)
            # Get the URL of the public site
            url = "http://{}.s3-website.{}.amazonaws.com/".format(bucket, s3.meta.region_name)

            # Get the tag set for the bucket
            try:
                response = s3.get_bucket_tagging(Bucket=bucket)
            except:
                print(f"Bucket {bucket} has no tags")
                continue
            tags = {tag['Key']: tag['Value'] for tag in response['TagSet']}

            # Check if the content of the site matches the tag of the bucket
            try:
                with urllib.request.urlopen(url, timeout=3) as response:
                    content = response.read().decode('utf-8')
                    student = tags.get('Name')
                    if already_passed(student):
                        print(f"{student} already passed")
                        continue
                    index = content.find(tags.get('Name'))
                    if index == -1:
                        print("The content of the site does not match the tag of the bucket.")
                    else:
                        print(f"The content of the site matches the tag Name = {tags.get('Name')} of the bucket.")
                        try:
                            s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{student}/")
                            print(f"{student} folder created in the ica0017-results bucket")
                            # Create a list of tags
                            tags = [{'Key': 'passed', 'Value': 'true'}, {'Key': 'author', 'Value': 'lambda'}]

                            # Upload the file to S3
                            s3.upload_file("passed.txt", 'ica0017-results', f'{lab}/{student}/passed.txt')

                            # Add tags to the uploaded file
                            s3.put_object_tagging(Bucket='ica0017-results', Key=f'{lab}/{student}/passed.txt', Tagging={'TagSet': tags})
                            print(f'passed.txt has been uploaded to {lab}/{student}/passed.txt with tags')
                        except Exception as e:
                            print(f"Error creating {student} folder in the ica0017-results bucket: {e}")
            except:
                print("Unable to retrieve the content of the site. Check that website is available to you.")
        except:
            print(f"Public site hosting is not enabled for the bucket {bucket}.")
            continue
    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'Hello, DONE!'})
    }

#lambda_handler("asd", "test")