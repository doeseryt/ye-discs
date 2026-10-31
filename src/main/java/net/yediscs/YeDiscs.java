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

    // one disc per album, named for that album's most popular track
    private static final String[] TRACKS = {
        "through_the_wire", "gold_digger", "stronger", "heartless",
        "runaway", "nias_in_paris", "black_skinhead", "famous",
        "ghost_town", "follow_god", "hurricane", "true_love",
        "carnival", "five_30", "bully"
    };

    @Override
    public void onInitialize() {
        for (String track : TRACKS) {
            registerDisc(track);
        }
    }

    private void registerDisc(String track) {
        Identifier soundId = Identifier.of(MOD_ID, track);
        SoundEvent registeredSound = Registry.register(Registries.SOUND_EVENT, soundId, SoundEvent.of(soundId));

        Identifier songId = Identifier.of(MOD_ID, track);
        RegistryKey<net.minecraft.block.jukebox.JukeboxSong> songKey =
                RegistryKey.of(RegistryKeys.JUKEBOX_SONG, songId);

        Identifier itemId = Identifier.of(MOD_ID, "ye_disc_" + track);
        Rarity rarity = "runaway".equals(track) || "carnival".equals(track) ? Rarity.EPIC : Rarity.RARE;
        Item disc = new Item(new Item.Settings()
                .maxCount(1)
                .rarity(rarity)
                .jukeboxPlayable(songKey));
        Registry.register(Registries.ITEM, itemId, disc);
    }
}
