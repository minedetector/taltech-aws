import boto3
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

reset_lambda_function_cache("cleared-for-exam")

# Initialize the S3 client
s3 = boto3.client('s3')

# Set the S3 bucket name
bucket_name = 'ica0017-results'

# List all objects in the bucket
response = s3.list_objects_v2(Bucket=bucket_name)

# Create a set of all the folder paths
students_and_passed_labs = {}

lab = "cleared_for_exam"
labs_to_check = ["lab2", "lab3", "lab4", "lab5"]

def already_passed(student):
    # Check if the passed.txt file exists in the folder
    try:
        s3.head_object(Bucket='ica0017-results', Key=f'{lab}/{student}/passed.txt')
        #print(f'{student} has already passed {lab}')
        # Get the tags of the file
        tags = s3.get_object_tagging(Bucket='ica0017-results', Key=f'{lab}/{student}/passed.txt')['TagSet']
        passed = False
        author = False
        #iterate through the tags and check if the passed and author tags are correct
        for tag in tags:
            if tag['Key'] == 'passed' and tag['Value'] == 'true':
                passed = True
            if tag['Key'] == 'author' and tag['Value'] == 'lambda':
                author = True
        if passed and author:
            return True
        else:
            print('ALERT the pass file is not legitimate')
    except:
        pass
    return False

def create_passed_file(uni_id):
    if not (already_passed(uni_id)):
        try:
            s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{uni_id}/")
            #print(f"{uni_id} folder created in the ica0017-results bucket")
            # Create a list of tags
            tags = [{'Key': 'passed', 'Value': 'true'}, {'Key': 'author', 'Value': 'lambda'}]

            # Upload the file to S3
            s3.upload_file("passed.txt", 'ica0017-results', f'{lab}/{uni_id}/passed.txt')

            # Add tags to the uploaded file
            s3.put_object_tagging(Bucket='ica0017-results', Key=f'{lab}/{uni_id}/passed.txt', Tagging={'TagSet': tags})
            #print(f'passed.txt has been uploaded to {lab}/{uni_id}/passed.txt\n')
        except Exception as e:
            print(f"Error creating {uni_id} folder in the ica0017-results bucket: {e}")

def check_labs(event):
    # Loop through the objects in the bucket
    for obj in response['Contents']:
        if ("cleared_for_exam" in obj["Key"]):
            continue
        # Get the path of the object
        path = obj['Key']
        # Check if the path ends with "passed.txt"
        if path.endswith("passed.txt"):
            # Get the folder path
            folder_path = path.rsplit('/', 1)[0]
            lab_nr, student = folder_path.split("/")
            students_and_passed_labs.setdefault(student, []).append(lab_nr)

    if ("User" in event) and event["User"] in students_and_passed_labs:
        student = event['User']
        passed_labs = students_and_passed_labs[student]
        if all(item in passed_labs for item in labs_to_check):
            print(f"Congratulations {student} you have passed all of the labs")
            create_passed_file(student)
        else:
            print(f"{student} has passed labs {students_and_passed_labs}")
    else:
        for student, passed_labs in students_and_passed_labs.items():
            passed_labs_count = len(passed_labs)
            passed_labs_string = ", ".join(passed_labs)

            if all(item in passed_labs for item in labs_to_check):
                print(f"{student} has passed all tests\n")
                create_passed_file(student)
            else:
                print(f"{student} has currently passed {passed_labs_count} lab(s), which are {passed_labs_string}\n")

def lambda_handler(event, context):
    check_labs(event)

lambda_handler({"Users": "kiales"}, "test")