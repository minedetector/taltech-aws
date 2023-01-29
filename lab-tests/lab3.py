import boto3
import urllib.request
import subprocess

# Initialize the s3 client
s3 = boto3.client('s3')

lab = "lab3"

# Get a list of all buckets with the prefix ica0017
response = s3.list_buckets()
buckets = [bucket['Name'] for bucket in response['Buckets'] if bucket['Name'].startswith('ica0017')]

# Iterate over the buckets and check if they have public site hosting enabled
for bucket in buckets:
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
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                student = tags.get('Name')
                index = content.find(tags.get('Name'))
                if index == -1:
                    print("The content of the site does not match the tag of the bucket.")
                else:
                    print("The content of the site matches the tag of the bucket.")
                    try:
                        s3.put_object(Bucket='ica0017-results', Key=f"{lab}/{student}/")
                        print(f"{student} folder created in the ica0017-results bucket")
                        # Create a list of tags
                        tags = [{'Key': 'passed', 'Value': 'true'}, {'Key': 'author', 'Value': 'lambda'}]

                        # Create passed.txt file
                        subprocess.run(["touch", "passed.txt"])

                        # Upload the file to S3
                        s3.upload_file("passed.txt", 'ica0017-results', f'{lab}/{student}/passed.txt')

                        # Add tags to the uploaded file
                        s3.put_object_tagging(Bucket='ica0017-results', Key=f'{lab}/{student}/passed.txt', Tagging={'TagSet': tags})
                        print(f'passed.txt has been uploaded to {lab}/{student}/passed.txt with tags')
                    except Exception as e:
                        print(f"Error creating {student} folder in the ica0017-results bucket: {e}")
        except:
            print("Unable to retrieve the content of the site.")
    except:
        print(f"Public site hosting is not enabled for the bucket {bucket}.")
        continue

