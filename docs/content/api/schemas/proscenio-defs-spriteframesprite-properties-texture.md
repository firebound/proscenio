# Texture Schema

```txt
https://space-wizard-studios.github.io/proscenio/schemas/proscenio.schema.json#/$defs/SpriteFrameSprite/properties/texture
```

Optional per-sprite texture filename, resolved relative to the .proscenio document. Mirrors the polygon-sprite field. Importers fall back to the top-level `atlas` field when absent.

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                              |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :-------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [proscenio.schema.json\*](../../../../out/proscenio.schema.json "open original schema") |

## texture Type

merged type ([Texture](proscenio-defs-spriteframesprite-properties-texture.md))

any of

* [Untitled string in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-anyof-0.md "check type definition")

* [Untitled null in Proscenio character](proscenio-defs-spriteframesprite-properties-texture-anyof-1.md "check type definition")
