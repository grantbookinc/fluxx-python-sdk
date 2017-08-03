# Fluxx API Python Client
Simple wrapper around the Fluxx GMS API.

## Installation
```bash
$ pip install fluxx-python-sdk
```

## Example Usage

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
