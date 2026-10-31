# YE Discs

A Fabric mod for Minecraft: **one disc per Kanye West album era** — fifteen original instrumental music discs, each styled and synthesized in the mood of its album, playable in any jukebox.

> Fan tribute mod. All music is **original, synthesized instrumental audio** — no Kanye West recordings, samples, or artwork are included. Album names identify the era each instrumental evokes.

## Versions

- Minecraft **1.20.1** (Java 17)
- Minecraft **1.21.1** (Java 21)

Loader: Fabric (Fabric API required).

## The discs (one per album)

| # | Disc | Era mood |
|---|------|----------|
| 1 | The College Dropout | sped-up soul chipmunk loop, dusty boom-bap |
| 2 | Late Registration | soul strings + orchestral swells |
| 3 | Graduation | electro-house stomp, filtered arena riff |
| 4 | 808s & Heartbreak | icy FM keys, huge 808 sub, frozen minimalism |
| 5 | My Beautiful Dark Twisted Fantasy | hammered piano ostinato, giant drums |
| 6 | Watch the Throne | operatic brass fanfare, gilded 808s |
| 7 | Yeezus | acid bass, drill kicks, industrial noise |
| 8 | The Life of Pablo | gospel choir pads + sudden soul chops |
| 9 | ye | Wyoming two-chord stillness, fuzz shimmer break |
| 10 | Jesus Is King | organ chords, gospel 6/8, handclaps |
| 11 | Donda | stadium lament strings, booming 808 |
| 12 | Donda 2 | unfinished-stem loops, gaps, skeletal drums |
| 13 | Vultures 1 | sinister bass hum, wheezing organ stomp |
| 14 | Vultures 2 | hollowed jazzy keys, slowed melancholy tail |
| 15 | BULLY era | washed-out soul grief, music-box motif |

## The special craft — vinyl pressing

Every disc is pressed like a record:

```
C P C
P I P
C P C
```

- **C** — Coal (the pressing heat)
- **P** — Paper (the blank vinyl)
- **I** — an item that identifies the album:
  - The College Dropout → Leather (the bear's jacket)
  - Late Registration → Note Block
  - Graduation → Firework Rocket
  - 808s & Heartbreak → Packed Ice
  - MBDTF → Netherite Scrap
  - Watch the Throne → Gold Block
  - Yeezus → Iron Block
  - The Life of Pablo → Pink Dye
  - ye → Grass Block
  - Jesus Is King → Lapis Lazuli
  - Donda → Black Wool
  - Donda 2 → Gray Dye
  - Vultures 1 → Bone
  - Vultures 2 → Bone Meal
  - BULLY era → Gold Ingot

## Build

```bash
./gradlew build   # for the version set in gradle.properties
```

For the 1.21.1 build, the same sources are compiled with 1.21.1 mappings/dependencies — see the [`1.21` branch](https://github.com/doeseryt/ye-discs/tree/1.21).

**Download:** [Modrinth — YE Discs](https://modrinth.com/mod/ye-discs)

## License

MIT — see `LICENSE`. The music is original synthesized audio, also MIT. Disc textures are programmatic pixel art with era accent colors.
