# Tests logic

## Lab2

Go through the running instances and get their tags and IP addresses.
- The tag `Name` needs to exist

Next see if there is already an existing `passed.txt` file inside the `ica0017-results/lab2/{name}`
bucket that has the required tags of `Passed` and `Author`.
- `name` should be your UNI-id aka the value of tag `Name`

If it doesn't then curl the public IP address of the instance and if the `Name` tags value matches
what is written on the page ( in the index.html file ) then it uses the `Name` tags value to create
a folder in `ica0017-results/lab2`. Puts a `passed.txt` file inside it with the correct tags.

## Lab3

Go through all of the buckets with the prefix `ica0017` existing in the account.
Check wether they have static website hosting enabled or not.
After which check if the tag exists.
Finally check if the contents on the hosted page mention the tag `Name` value.

If all of the aformentioned checks pass a new folder is created in `ica0017-results/lab3` that uses
the value of the tag `Name` and creates a `passed.txt` file in it.

## Lab4

Get all of the public subets that have a tag with the kay `User` attached and iterate through them 1-by-1.
If the key `User` is defined for the test then only test
their resources, otherwise test everyones.

Next step is to test whether the public subnet has internet access
and that the private subnet does not have internet access.

If both previous checks pass then get the public IP of the
website instance and check its contents.
Also make sure that the private instance has no public IP defined.

If all of the aformentioned checks pass then create the passed.txt file for the student.