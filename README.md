# cf-macro-jsonet

Run arbitrary [jsonnet](https://jsonnet.org) code in your CloudFormation templates

## Basic Usage

Place jsonnet code as a literal bock anywhere in your template, the literal
block will be replaced with its evaluation.

Macro paramters are added to the snippet scope individually. These extra
variables are added to the snipped scope.

- `params`: the top-level template parameters
- `template`: the entire template
- `account_id`: AWS account ID
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

## Development

- Compile the Python jsonnet bindings into a replica of the
  lambda environemnt

  ```
  $ docker run -it --rm -v $PWD/src:/var/task lambci/lambda:build-python3.6 pip install -t . jsonnet
  ```

- Use the [SAM cli](https://github.com/awslabs/aws-sam-cli) to tests the code locally

  ```
  $ sam local invoke --event ./tests/test.json
  ```

- Deploy to AWS Lambda

  ```
  $ sam package --template-file template.yml --s3-bucket ${BUCKET_NAME} --output-template /tmp/template.yml
  $ sam deploy --template-file /tmp/template.yml --stack-name cf-macro-jsonnet --capabilities CAPABILITY_IAM
  ```

## TODO

- hook into jsonnet `import` mechanism in some way
- more meaningful examples
- proper testing


## License

[MIT License](http://www.opensource.org/licenses/MIT)

## Author

[Andrea Bedini](https://github.com/andreabedini), [KZN Group](https://kzn.io)

