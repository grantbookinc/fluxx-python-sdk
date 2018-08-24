# Fluxx API Python Client
Simple wrapper around the Fluxx GMS API.

## Installation
```bash
$ pip install fluxx_wrapper
```

## TODO
  - change subdomain to full url
  - better in tool command documentation


## Config
The command line tool expects three environmental variables to be set:
  - url of the fluxx instance (url segment before .fluxx.io)
  - application ID
  - application secret

It is required to set these variables using a unique identifier
and the following suffixes, respectively:
  _INSTANCE
  _CLIENT
  _SECRET

For example, if we have a Fluxx instance with url "demo.fluxx.io", application id "ABC",
and application secret "123", we would set the following:

  DEMO_INSTANCE = 'demo.fluxx.io'  
  DEMO_CLIENT = 'ABC'  
  DEMO_SECRET = '123'  


## Example Usage as Library

```python
from fluxx_wrapper import FluxxClient, FluxxError

# initialize client
fluxx = FluxxClient(
    os.getenv('YOUR_INSTANCE'),
    os.getenv('YOUR_CLIENT_ID'),
    os.getenv('YOUR_CLIENT_SECRET'),
    version='v2',
    style='full'
)

# list model attributes
fields = fluxx.model_attribute.list({
    cols=['attribute_type', 'description', 'legacy_name', 'model_type'],
    per_page=10000
})

  # example workflow, set empty description to regex-matching legacy names
for field in fields:
    if not 'description' in field:
        legacy_name = field['legacy_name']

        if re.match(r'\(.*`.*`\)', legacy_name):
            legacy_name = legacy_name.split('`')[1]

        desc = legacy_name.replace('_', ' ')
        desc = titlecase(desc)

        body = {'description': desc}

        try:
            updated = fluxx.model_attribute.update(field['id'], body)
        except FluxxError as e:
            print(e)


    print(updated['description'])
```
