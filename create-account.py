import subprocess
import json
import sys

taltech_students_permission_set_arn = 'arn:aws:sso:::permissionSet/ssoins-650816aa11fd1188/ps-53d72fc1862a2e34'
taltech_teachers_permission_set_arn = 'arn:aws:sso:::permissionSet/ssoins-650816aa11fd1188/ps-389b48caec9faba9'
taltech_researchers_permission_set_arn = 'arn:aws:sso:::permissionSet/ssoins-650816aa11fd1188/ps-2a52296e98d0dc69'

taltech_subjects_account_group_id = 'ou-f56r-yjx8ztgu'
taltech_researchers_account_group_id = 'ou-f56r-mmg2wk9c'

def main(account_owner_email, account_name, account_purpose):
    if account_purpose not in ['subject', 'research']:
        raise ValueError("Wrong account purpose, choose either subject or research")

    create_account(account_owner_email, account_name)

    instance_arn, instance_id = get_aws_sso_insatance_data()

    account_id = get_account_id(account_name)

    if account_purpose == "subject":
        # Define the students group name that was created in the Active Directory
        # The name has to match exactly otherwise this will fail
        students_group_name = f"UNISEC-students-{account_name}"

        students_group_id = get_group_id(students_group_name, instance_id)

        assign_group_to_account(instance_arn, students_group_id, taltech_students_permission_set_arn, account_id)

        teachers_group_name = f"SEC-teachers-{account_name}"

        teachers_group_id = get_group_id(teachers_group_name, instance_id)

        assign_group_to_account(instance_arn, teachers_group_id, taltech_teachers_permission_set_arn, account_id)

        move_account_to_group(account_id, taltech_subjects_account_group_id)

    elif account_purpose == "research":
        researchers_group_name = f"SEC-scientists-{account_name}"

        researchers_group_id = get_group_id(researchers_group_name, instance_id)

        assign_group_to_account(instance_arn, researchers_group_id, taltech_teachers_permission_set_arn, account_id)

        move_account_to_group(account_id, taltech_researchers_account_group_id)

    print(account_id)

def create_account(account_owner_email, account_name):
    account_creation_command = f'''
    aws organizations create-account \
        --email {account_owner_email} \
        --account-name {account_name} \
        --role-name OrganizationAccountAccessRole \
        --iam-user-access-to-billing "ALLOW" \
    '''

    subprocess.run(account_creation_command.split())

    return account_name

def get_json_object(command):

    command_output = subprocess.check_output(command.split())
    json_output = json.loads(command_output)

    return json_output 


def get_aws_sso_insatance_data():
    get_instance = '''
        aws sso-admin list-instances --output json
    '''
    instance_data = get_json_object(get_instance)

    instance_arn = instance_data["Instances"][0]["InstanceArn"]
    instance_id = instance_data["Instances"][0]["IdentityStoreId"]

    return instance_arn, instance_id

def get_account_id(account_name):
    get_account_ids = '''
        aws organizations list-accounts --output json
        '''
    
    all_accounts_data = get_json_object(get_account_ids)

    # Filter out only the new account
    new_account_data = [x for x in all_accounts_data["Accounts"] if x["Name"]==f"{account_name}"]

    new_account_id = new_account_data[0]["Id"]

    return new_account_id

def get_group_id(group_name, instance_id):
    get_group_id_command = f'''
        aws identitystore list-groups \
            --identity-store-id {instance_id} \
            --filter AttributePath="DisplayName",AttributeValue="{group_name}" \
            --output json
    '''

    group_data = get_json_object(get_group_id_command)

    group_id = group_data["Groups"][0]["GroupId"]

    return group_id

def assign_group_to_account(instance_arn, group_id, permission_set_arn, account_id):
    command = f'''
        aws sso-admin create-account-assignment \
            --instance-arn '{instance_arn}' \
            --permission-set-arn '{permission_set_arn}' \
            --principal-id '{group_id}' \
            --principal-type 'GROUP' \
            --target-id '{account_id}' \
            --target-type AWS_ACCOUNT
    '''

    subprocess.run(command.split())

# Moves the account from the Root OU (Organizational Unit in AWS Organizations) to the correct OU
def move_account_to_group(account_id, destination_id):
    command = f'''
        aws organizations move-account \
            --account-id {account_id} \
            --source-parent-id r-f56r \
            --destination-parent-id {destination_id}
    '''
    
    subprocess.run(command.split())

account_owner_email = sys.argv[1]
account_name = sys.argv[2]
account_purpose = sys.argv[3]

main(account_owner_email, account_name, account_purpose)
