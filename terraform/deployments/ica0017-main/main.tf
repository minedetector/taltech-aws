module "class_vpc" {
  source = "../../modules/vpc"

  name       = "ICA0017-VPC"
  cidr_block = "172.0.0.0/16"
  create_igw = true
}

module "class_public_subnet" {
  source = "../../modules/subnet"

  name                 = "ICA0017-public-subnet"
  vpc_id               = module.class_vpc.vpc_id
  cidr_block           = "172.0.0.0/24"
  public_ip_by_default = true
  routes = {
    internet_access = {
      cidr_block = "0.0.0.0/0"
      gateway_id = module.class_vpc.igw_id
    }
  }
  subnet_type = "public"
}

module "results_bucket" {
  source = "../../modules/bucket"

  name = "ica0017-results"
}

module "lab6_bucket" {
  source = "../../modules/bucket"

  name = "ica0017-lab6-states"
}

module "pass_students_policy" {
  source = "../../modules/iam/pass-students-policy"

  name               = "pass-students"
  results_bucket_arn = module.results_bucket.bucket_arn
}

module "stop_instance_after_hour_role" {
  source = "../../modules/iam/stop-instance-role"

  name = "stop-instances-after-hour"
}

# TODO Change lambda function module to be more generic and not just for lab tests
module "stop_instance_after_hour_lambda_function" {
  source = "../../modules/test-lab-lambda-function"

  name              = "stop_instance_after_hour"
  source_file_path  = "../../files/instanceStopFunction.py"
  zip_file_path     = "../../files/instanceStopFunction.zip"
  role_arn          = module.lab6_role.role_arn
  trigger_frequency = "rate(1 hour)"
}

module "downscale_asg_role" {
  source = "../../modules/iam/downscale-asgs-role"

  name = "downscale-asgs-after-hour"
}

module "downscale_asg_lambda_function" {
  source = "../../modules/test-lab-lambda-function"

  name              = "downscale_asgs"
  source_file_path  = "../../files/downscale_asgs.py"
  zip_file_path     = "../../files/downscale_asgs.zip"
  role_arn          = module.downscale_asg_role.role_arn
  trigger_frequency = "rate(1 hour)"
}

module "lab2_role" {
  source = "../../modules/iam/test-lab2-role"

  name                     = "test-lab2"
  pass_students_policy_arn = module.pass_students_policy.policy_arn
}

module "lab2" {
  source = "../../modules/test-lab-lambda-function"

  name              = "test-lab2"
  source_file_path  = "../../files/lab2.py"
  zip_file_path     = "../../files/lab2.zip"
  role_arn          = module.lab2_role.role_arn
  trigger_frequency = "rate(5 minutes)"
}

module "lab3_role" {
  source = "../../modules/iam/test-lab3-role"

  name                     = "test-lab3"
  pass_students_policy_arn = module.pass_students_policy.policy_arn
}

module "lab3" {
  source = "../../modules/test-lab-lambda-function"

  name              = "test-lab3"
  source_file_path  = "../../files/lab3.py"
  zip_file_path     = "../../files/lab3.zip"
  role_arn          = module.lab3_role.role_arn
  trigger_frequency = "rate(5 minutes)"
}

module "lab4_role" {
  source = "../../modules/iam/test-lab4-role"

  name                     = "test-lab4"
  pass_students_policy_arn = module.pass_students_policy.policy_arn
}

module "lab4" {
  source = "../../modules/test-lab-lambda-function"

  name              = "test-lab4"
  source_file_path  = "../../files/lab4.py"
  zip_file_path     = "../../files/lab4.zip"
  role_arn          = module.lab4_role.role_arn
  trigger_frequency = "rate(5 minutes)"
}

module "lab5_role" {
  source = "../../modules/iam/test-lab5-role"

  name                     = "test-lab5"
  pass_students_policy_arn = module.pass_students_policy.policy_arn
}

module "lab5" {
  source = "../../modules/test-lab-lambda-function"

  name              = "test-lab5"
  source_file_path  = "../../files/lab5.py"
  zip_file_path     = "../../files/lab5.zip"
  role_arn          = module.lab5_role.role_arn
  trigger_frequency = "rate(5 minutes)"
}

module "lab6_role" {
  source = "../../modules/iam/test-lab6-role"

  name                     = "test-lab6"
  pass_students_policy_arn = module.pass_students_policy.policy_arn
  lab_bucket_arn           = module.lab6_bucket.bucket_arn
}

module "lab6" {
  source = "../../modules/test-lab-lambda-function"

  name              = "test-lab6"
  source_file_path  = "../../files/lab6.py"
  zip_file_path     = "../../files/lab6.zip"
  role_arn          = module.lab6_role.role_arn
  trigger_frequency = "rate(5 minutes)"
}

module "cleared_for_exam_role" {
  source = "../../modules/iam/cleared-for-exam-role"

  name                     = "cleared-for-exam"
  pass_students_policy_arn = module.pass_students_policy.policy_arn
}

module "cleared_for_exam" {
  source = "../../modules/test-lab-lambda-function"

  name              = "cleared-for-exam"
  source_file_path  = "../../files/cleared_for_exam.py"
  zip_file_path     = "../../files/cleared_for_exam.zip"
  role_arn          = module.cleared_for_exam_role.role_arn
  trigger_frequency = "rate(5 minutes)"
}