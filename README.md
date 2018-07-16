# python-console-keycloak-example

A client application, configured as an OIDC client in [Keycloak](https://www.keycloak.org/) that shows how to obtain access grants, using the OAuth's [Resource Owner Password Credentials](https://tools.ietf.org/html/rfc6749#section-1.3.3)


## Keycloak configuration

Create a new OIDC client in keycloak, with "Access Type" set to "confidential" and optionally disable the option "Standard Flow Enabled" and save it.
Click again on the client and go under Credentials tab, you will see the secret.

## Python script configuration
Replace KEYCLOAK-HOST, REALM-NAME, CLIENT-ID, CLIENT-SECRET in the auth.py file with the info given by keycloak

```code
keycloak_realm_url = 'https://<KEYCLOAK-HOST>/auth/realms/<REALM-NAME>/'
client_id = '<CLIENT-ID>'
client_secret = '<CLIENT-SECRET>'
token_endpoint = keycloak_realm_url + 'protocol/openid-connect/token'
```

Execute the script to get access grants
```shell
python auth.py
```

A convenient bash script was created to set the environment variable ACCESS_TOKEN that can be used in subsequent API calls.
```shell
#Sets an environment variable ACCESS_TOKEN that can be used in the curl script below
source setenv-with-access-token.sh

#Change the curl to access your protected resource
curl -H "Authorization: Bearer $ACCESS_TOKEN" "http://localhost:8080/my-protected-resource"
```
