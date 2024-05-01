# publication email request service (pers)

PERS is a Python CLI application for sending email requests for publications.

## Development

- To preview a list of available Makefile commands: `make help`
- To install with dev dependencies: `make install`
- To update dependencies: `make update`
- To run unit tests: `make test`
- To lint the repo: `make lint`
- To run the app: `pipenv run my_app --help`

## Environment variables

### Required

```shell
ELEMENTS_ENDPOINT=### API endpoint of Symplectic Elements
ELEMENTS_USER=### Username associated with Symplectic Elements API user account
ELEMENTS_PASSWORD=### Password associated with Symplectic Elements API user account 
QUOTAGUARD_STATIC_URL=### A Proxy URL required to access the Symplectic Elements API
PERS_DATABASE_CONNECTION_STRING=### Connection string for PERS database
SENTRY_DSN=### If set to a valid Sentry DSN, enables Sentry exception monitoring. This is not needed for local development.
WORKSPACE=### Set to `dev` for local development, this will be set to `stage` and `prod` in those environments by Terraform.
```

### Optional

_Delete this section if it isn't applicable to the PR._

```
# Description for optional environment variable
<OPTIONAL_ENV>=
```




