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