# Verimatrix XTD and Counterspy

This action integrates Verimatrix Extended Threat Defense and Counterspy into your GitHub build workflow. It automates
the protection of your Android and iOS apps so you can run it whenever a new version
of your application is built.

[Verimatrix XTD and Counterspy](https://portal.platform.verimatrixcloud.net/) are a zero-code in-app protection services. They protect your apps from
reverse engineering and attack through a layered security approach. Protection layers include
obfuscation, environmental checks and binary integrity checks.

All **XTD** subscription tiers support this action, while for **Counterspy** you need a Standard subscription.

## API Keys

In order to use the action, an API key is required. This can be created and retrieved in [XTD or Counterspy](https://portal.platform.verimatrixcloud.net/)
portal under "Settings" menu, in the "API Key Manager" panel. Simply click the "Generate New API Key" button for generating a new key.

```json
{
  "appClientId": "7m.........0s5i",
  "appClientSecret": "cm1m65g.......jt",
  "encodedKey": "Njd.........tbzBzNW.......0"
}
```

Once generated, you are adviced to add the value of the 'encodedKey' field to your project as action secrets and reference it in your workflow configuration.

## Input

Action requires the following parameters and corresponding values:

| Name                | Required | Description                                                           |
| ------------------- | -------- | --------------------------------------------------------------------- |
| `api-key-secret`    | ✅       | The `encodedKey` from your API key JSON                               |
| `app-file`          | ✅       | Path to the app file (`.apk`, `.aab`, or `.zip`)                      |
| `api-gateway-url`   | ❌       | (Optional) Custom API Gateway URL                                     |
| `access-token-url`  | ❌       | (Optional) Custom Access Token URL                                    |
| `subscription-type` | ❌       | (Optional) Override for subscription type (e.g., `XTD`, `COUNTERSPY`) |

## Outputs

Action produces a single output:

| Name             | Description                                               |
| ---------------- | --------------------------------------------------------- |
| `protected-file` | The filename of the protected app downloaded from the API |

The `protected-file` name can be used with [upload-artifact](https://github.com/actions/upload-artifact) action
to save the file as a build artifact.

## Usage

```yaml
- name: Application Protection
  id: app-protect
  uses: verimatrix/app-protect@v2
  with:
    api-key-secret: ${{ secrets.API_ENCODED_KEY }}
    app-file: ${{ github.event.inputs.file }}
```
