package net.yediscs;

import net.fabricmc.api.ModInitializer;
import net.minecraft.item.Item;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.sound.SoundEvent;
import net.minecraft.util.Identifier;
import net.minecraft.util.Rarity;

public class YeDiscs implements ModInitializer {

    public static final String MOD_ID = "ye_discs";

    // album ids in discography order
    private static final String[] ALBUMS = {
        "college_dropout", "late_registration", "graduation", "808s",
        "mbdtf", "watch_the_throne", "yeezus", "tlop", "ye", "jik",
        "donda", "donda2", "vultures1", "vultures2", "bully_era"
    };

    @Override
    public void onInitialize() {
        for (String album : ALBUMS) {
            registerDisc(album);
        }
    }

    private void registerDisc(String album) {
        Identifier soundId = Identifier.of(MOD_ID, album);
        SoundEvent registeredSound = Registry.register(Registries.SOUND_EVENT, soundId, SoundEvent.of(soundId));

        Identifier songId = Identifier.of(MOD_ID, album);
        RegistryKey<net.minecraft.block.jukebox.JukeboxSong> songKey =
                RegistryKey.of(RegistryKeys.JUKEBOX_SONG, songId);

        Identifier itemId = Identifier.of(MOD_ID, "ye_disc_" + album);
        Rarity rarity = "mbdtf".equals(album) || "donda".equals(album) ? Rarity.EPIC : Rarity.RARE;
        Item disc = new Item(new Item.Settings()
                .maxCount(1)
                .rarity(rarity)
                .jukeboxPlayable(songKey));
        Registry.register(Registries.ITEM, itemId, disc);
    }
}
