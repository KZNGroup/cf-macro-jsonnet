# cf-macro-jsonet

Evaluate arbitrary [jsonnet](https://jsonnet.org) code in your
CloudFormation templates.

## Basic Usage

Place jsonnet code as a text block anywhere in your template, the text
block will be replaced with its evaluation.

The following bindings are added to the snippet scope:

- `templateParams`: the top-level template parameters
- `template`: the entire template
- `accountId`: AWS account ID
- `region`: AWS Region

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: [Jsonnet]
Resources:
  S3Bucket:
    Type: "AWS::S3::Bucket"
    Properties:
      Tags: |
        #!jsonnet
        local tags = {
          Project: 'take-over-the-world',
          Stage: 'testing'
        };
        [{ Key: k, Value: tags[k] } for k in std.objectFields(tags)]
```

## Using a library

The template parameter JsonnetLibraryUri can be used to provide an URI
to a zip-file that will act as a search path for jsonnet imports.

Example:

- Upload to S3 a Zip file containing a file `utils.jsonnet` with the
  following content:

  ```
  {
    toEntries(obj): [{ Key: k, Value: obj[k] } for k in std.objectFields(obj)]
  }
  ```

- Now you can use `toEntries` like the following

  ```yaml
  AWSTemplateFormatVersion: "2010-09-09"
  Transform: [Jsonnet]
  JsonnetLibraryUri: s3://path/to/zip/file/above
  Resources:
    S3Bucket:
      Type: "AWS::S3::Bucket"
      Properties:
        Tags: |
          #!jsonnet
          local utils = import "utils.jsonnet";
          utils.toEntries({
            Project: 'take-over-the-world',
            Stage: 'testing'
          })
    ```

## Development

- Compile the Python jsonnet bindings into a replica of the
  lambda environemnt

  ```
  $ docker run -it --rm -v $PWD/src:/var/task lambci/lambda:build-python3.6 pip install -t . jsonnet
  ```

- Use the [SAM cli](https://github.com/awslabs/aws-sam-cli) to tests the code locally

  ```
  $ sam local invoke --event ./tests/event.json
  ```

- Deploy to AWS Lambda

  ```
  $ sam package --template-file template.yml --s3-bucket ${BUCKET_NAME} --output-template /tmp/template.yml
  $ sam deploy --template-file /tmp/template.yml --stack-name cf-macro-jsonnet --capabilities CAPABILITY_IAM
  ```

## TODO

- more meaningful examples
- proper testing


## License

[MIT License](http://www.opensource.org/licenses/MIT)

## Author

[Andrea Bedini](https://github.com/andreabedini), [KZN Group](https://kzn.io)

