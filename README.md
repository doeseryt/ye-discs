# YE Discs

A Fabric mod for Minecraft: **one disc per Kanye West album — the album's most popular track**. Fifteen original instrumental music discs, each named for the song that defines its album and synthesized to evoke that track's production, playable in any jukebox.

> Fan tribute mod. All music is **original, synthesized instrumental audio** — no Kanye West recordings, samples, or artwork are included. Track and album names identify the songs each instrumental evokes.

## Versions

- Minecraft **1.20.1** (Java 17)
- Minecraft **1.21.1** (Java 21)

Loader: Fabric (Fabric API required).

## The discs (most popular track per album)

| # | Album | Track disc | Sound mood |
|---|-------|-----------|------------|
| 1 | The College Dropout | Through the Wire | sped-up soul chipmunk loop, dusty boom-bap |
| 2 | Late Registration | Gold Digger | gospel-soul piano stabs, handclap bounce |
| 3 | Graduation | Stronger | vocoder electro riff, 4-on-the-floor, arena drop |
| 4 | 808s & Heartbreak | Heartless | icy 16th-note arp, huge 808, frozen minimalism |
| 5 | My Beautiful Dark Twisted Fantasy | Runaway | sparse dissonant piano, cavernous space |
| 6 | Watch the Throne | Ni**as in Paris | operatic synth-brass fanfare, gilded bounce |
| 7 | Yeezus | Black Skinhead | distorted industrial stabs, pounding four-on-the-floor |
| 8 | The Life of Pablo | Famous | chopped soul stab loop, heavy trap 808 bounce |
| 9 | ye | Ghost Town | hazy psychedelic groove, washed leads, luminous outro |
| 10 | Jesus Is King | Follow God | gospel drawbar organ, handclaps, choir ahs |
| 11 | Donda | Hurricane | pulsing minor synth arps, bouncy 808, anthemic release |
| 12 | Donda 2 | True Love | melancholic lo-fi piano, stem dropouts |
| 13 | Vultures 1 | Carnival | haunted funfair hoover riff, booming 808s |
| 14 | Vultures 2 | 530 | slowed hazy soul loop, pitched-down melancholy |
| 15 | BULLY (upcoming) | BULLY | washed-out soul grief, music-box motif |

## The special craft — vinyl pressing

Every disc is pressed like a record:

```
C P C
P I P
C P C
```

- **C** — Coal (the pressing heat)
- **P** — Paper (the blank vinyl)
- **I** — an item that identifies the track:
  - Through the Wire → Leather (the wired-shut jaw)
  - Gold Digger → Note Block (the piano loop)
  - Stronger → Firework Rocket (the arena drop)
  - Heartless → Packed Ice (frozen 808s)
  - Runaway → Netherite Scrap (a single dark take)
  - Ni**as in Paris → Gold Block (gilded Paris)
  - Black Skinhead → Iron Block (industrial brute)
  - Famous → Amethyst Shard (the scandal's shine)
  - Ghost Town → Grass Block (Wyoming fields)
  - Follow God → Lapis Lazuli (gospel blue)
  - Hurricane → Blue Ice (the storm's eye)
  - True Love → Gray Dye (unfinished stems)
  - Carnival → Bone (funfair bones)
  - 530 → Bone Meal (hollowed sequel)
  - BULLY → Gold Ingot (the washed gold)

## Build

```bash
./gradlew build   # for the version set in gradle.properties
```

For the 1.21.1 build, the same sources are compiled with 1.21.1 mappings/dependencies — see the [`1.21` branch](https://github.com/doeseryt/ye-discs/tree/1.21).

**Download:** [Modrinth — YE Discs](https://modrinth.com/mod/ye-discs)

## License

MIT — see `LICENSE`. The music is original synthesized audio, also MIT. Disc textures are programmatic pixel art with track accent colors.
