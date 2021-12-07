import subprocess
import json
import sys

taltech_students_permission_set_arn = 'arn:aws:sso:::permissionSet/ssoins-650816aa11fd1188/ps-53d72fc1862a2e34'
taltech_teachers_permission_set_arn = 'arn:aws:sso:::permissionSet/ssoins-650816aa11fd1188/ps-389b48caec9faba9'

def main(account_owner_email, account_name):
    create_account(account_owner_email, account_name)

    instance_arn, instance_id = get_aws_sso_insatance_data()

    account_id = get_account_id(account_name)

    students_group_name = f"UNISEC-{account_name}-students"

    students_group_id = get_group_id(students_group_name, instance_id)

    assign_group_to_account(instance_arn, students_group_id, taltech_students_permission_set_arn, account_id)

    teachers_group_name = f"UNISEC-{account_name}-teachers"

    teachers_group_id = get_group_id(teachers_group_name, instance_id)

    assign_group_to_account(instance_arn, teachers_group_id, taltech_teachers_permission_set_arn, account_id)

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

account_owner_email = sys.argv[1]
account_name = sys.argv[2]

main(account_owner_email, account_name)
