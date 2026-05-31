# Format Version Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/psd_manifest.schema.json#/properties/format_version
```

Bump on any breaking change to the shape of this document. v2 introduces the tag-driven taxonomy in the photoshop tag system (anchor, per-entry origin, blend\_mode, subfolder, kind: "mesh").

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                     |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [psd\_manifest.schema.json\*](../../../../out/psd_manifest.schema.json "open original schema") |

## format\_version Type

`integer` ([Format Version](psd_manifest-properties-format-version.md))

## format\_version Constraints

**constant**: the value of this property must be equal to:

```json
2
```
