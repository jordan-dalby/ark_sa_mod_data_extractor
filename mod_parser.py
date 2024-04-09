"""A parser for UE5 ARK SA DevKit that extracts data from your mod"""

import tempfile
import tarfile
import shutil
import uuid
import time
import json
import os
import unreal

MOD_DATA = {
    "MOD_ROOT_FOLDER": "/ResourceGatherers",
    "MOD_ID": "932365",
    "MOD_NAME": "Resource Gatherers",
    "CONTENT_PACK_ID": "ce54b3ba-f0a3-4c69-b52a-7e6c8c71bc55",
}

CONTENT_PACK_IDS = {
    "/Game/PrimalEarth/": "b32a3d73-9406-56f2-bd8f-936ee0275249",
    "/Game/ScorchedEarth/": "91bb3eb3-1ff5-4fc5-86f8-8cb158a2d977",
    "/Packs/Frontier/": "0d12c7e6-3ee4-4202-bd4a-1fa7c18b2bcc",
    MOD_DATA["MOD_ROOT_FOLDER"]: MOD_DATA["CONTENT_PACK_ID"],
}

OUTPUT_DIR = "E:\\Google Drive\\Python Scripts\\ArkSAModDataGenerator\\"
BEACON_NAMESPACE = uuid.UUID("82aa4465-85f9-4b9e-8d36-f66164cef0a6")


def uuid_from_path(path):
    """Converts a UE5 path into a V5 UUID"""
    for prefix, content_pack_id in CONTENT_PACK_IDS.items():
        if path.startswith(prefix):
            return str(
                uuid.uuid5(
                    BEACON_NAMESPACE, f"{content_pack_id.lower()}:{path.lower()}"
                )
            )
    return None


def make_tmp_dir():
    """Creates and returns a temporary directory"""
    tmp_dir = tempfile.mkdtemp()
    return tmp_dir


def remove_tmp_dir(tmp_dir):
    """Removes a previously created temporary directory"""
    shutil.rmtree(tmp_dir)


def dump_to_file(tmp_dir, file_name, contents):
    """Dumps data to a file given a directory, a file name, and its contents"""
    with open(os.path.join(tmp_dir, file_name), "w", encoding="utf-8") as text_file:
        text_file.write(contents)


class UnrealParser:
    """Parser used for getting data from the engine directly"""

    def __init__(self):
        pass

    def find_mda(self):
        """Find the mod data asset for this mod"""
        # pylint: disable=no-member
        assets = unreal.EditorAssetLibrary.list_assets(
            MOD_DATA["MOD_ROOT_FOLDER"], recursive=True
        )
        for asset_path in assets:
            asset_name = unreal.Paths.get_base_filename(asset_path)
            if asset_name.startswith("ModDataAsset"):
                return asset_path
        return None

    def get_additional_engram_blueprint_classes(self, asset_path):
        """Gets the additional engram blueprint classes field from the mod data asset"""
        # pylint: disable=no-member
        asset_object = unreal.EditorAssetLibrary.load_asset(asset_path)
        if asset_object:
            additional_engram_blueprint_classes = (
                asset_object.additional_engram_blueprint_classes
            )
            if additional_engram_blueprint_classes:
                return additional_engram_blueprint_classes
        else:
            print("Failed to load asset:", asset_path)
        return None


class BeaconBuilder:
    """A builder class that creates files in a format that can be imported into Beacon"""

    def __init__(self):
        self.engrams = []

    def add_engram(self, engram_data):
        """Adds an engram to the engrams array"""
        blueprintable = "blueprintable" if engram_data["blueprintable"] else None
        engram = {
            "group": "engrams",
            "engramId": engram_data["uuid"],
            "label": engram_data["primal_item_name"],
            "alternateLabel": None,
            "tags": [blueprintable],
            "availability": 3,
            "path": engram_data["engram_path"],
            "minVersion": 20000000,
            "lastUpdate": time.time(),
            "contentPackId": MOD_DATA["CONTENT_PACK_ID"],
            "contentPackName": MOD_DATA["MOD_NAME"],
            "entryString": engram_data["engram_class_name"],
            "requiredLevel": engram_data["required_level"],
            "requiredPoints": engram_data["required_engram_points"],
            "stackSize": engram_data["stack_size"],
        }

        recipe = []
        crafting_requirements = engram_data[
            "primal_item"
        ].base_crafting_resource_requirements
        for crafting_requirement in crafting_requirements:
            requirements = {
                "engramId": uuid_from_path(
                    crafting_requirement.resource_item_type.get_path_name()[:-2]
                ),
                "quantity": int(crafting_requirement.base_resource_requirement),
                "exact": crafting_requirement.crafting_require_exact_resource_type,
            }
            recipe.append(requirements)
        engram["recipe"] = recipe

        self.engrams.append(engram)

    def create_beacondata(self, folder_path, output_path):
        """Create the beacondata file"""
        with tarfile.open(output_path, "w:gz") as tar:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    tar.add(file_path, arcname=os.path.relpath(file_path, folder_path))

    def build(self, tmp_dir):
        """Build the contents of the json file that Beacon uses"""
        content_pack = [
            {
                "contentPackId": MOD_DATA["CONTENT_PACK_ID"],
                "gameId": "ArkSA",
                "marketplace": "CurseForge",
                "marketplaceId": MOD_DATA["MOD_ID"],
                "name": MOD_DATA["MOD_NAME"],
                "isConsoleSafe": False,
                "isDefaultEnabled": False,
                "minVersion": 20000000,
                "lastUpdate": time.time(),
            }
        ]
        content_packs = {"gameId": "ArkSA", "contentPacks": content_pack}
        content = {
            "payloads": [content_packs, {"gameId": "ArkSA", "engrams": self.engrams}]
        }
        dump_to_file(
            tmp_dir,
            f"{MOD_DATA['CONTENT_PACK_ID']}.json",
            json.dumps(content, indent=4),
        )

    def build_manifest(self, tmp_dir):
        """Build the manifest json file for Beacon"""
        manifest = {
            "version": 7,
            "minVersion": 7,
            "generatedWith": 20100301,
            "isFull": False,
            "files": [f"{MOD_DATA['CONTENT_PACK_ID']}.json"],
            "isUserData": True,
        }
        dump_to_file(tmp_dir, "Manifest.json", json.dumps(manifest, indent=4))

    def dump(self):
        """Dump all of the data to the temp directly and create the beacondata file"""
        temp_dir = make_tmp_dir()
        self.build(temp_dir)
        self.build_manifest(temp_dir)
        self.create_beacondata(
            temp_dir, OUTPUT_DIR + f"{MOD_DATA['MOD_NAME']}.beacondata"
        )
        remove_tmp_dir(temp_dir)


class StandardBuilder:
    """A standard builder that returns generic json extracted from the mod"""

    def __init__(self):
        self.engrams = []

    def add_engram(self, engram_data):
        """Adds an engram to the engram array"""
        engram = {
            "name": engram_data["primal_item_name"],
            "path": engram_data["engram_path"],
            "entryString": engram_data["engram_class_name"],
            "requiredLevel": engram_data["required_level"],
            "requiredPoints": engram_data["required_engram_points"],
            "stackSize": engram_data["stack_size"],
        }

        recipe = []
        crafting_requirements = engram_data[
            "primal_item"
        ].base_crafting_resource_requirements
        for crafting_requirement in crafting_requirements:
            requirements = {
                "resource": crafting_requirement.resource_item_type.get_path_name()[
                    :-2
                ],
                "quantity": int(crafting_requirement.base_resource_requirement),
                "exact": crafting_requirement.crafting_require_exact_resource_type,
            }
            recipe.append(requirements)
        engram["recipe"] = recipe

        self.engrams.append(engram)

    def build(self):
        """Build the generic json data"""
        build = {"engrams": self.engrams}
        return json.dumps(build, indent=4)

    def dump(self):
        """Dump the json data"""
        data = self.build()
        dump_to_file(OUTPUT_DIR, f"{MOD_DATA['MOD_NAME']}-data.json", data)


class Builder:
    """Base builder class, allows user to choose which output they prefer"""

    def __init__(self, builder):
        self.builder = builder

    def add_engram(self, engram):
        """Creates some valuable data that the builder classes use to
        create the json files"""
        blue_print_entry = engram.blue_print_entry
        # pylint: disable=no-member
        blue_print_entry_obj = unreal.load_object(
            None, blue_print_entry.get_path_name()
        )
        # pylint: disable=no-member
        blue_print_entry_obj_default = unreal.get_default_object(blue_print_entry_obj)

        engram_path = blue_print_entry_obj.get_path_name()[:-2]
        engram_data = {
            "uuid": uuid_from_path(engram_path),
            "engram_path": engram_path,
            "primal_item": blue_print_entry_obj_default,
            "primal_item_name": blue_print_entry_obj_default.descriptive_name_base,
            "blueprintable": blue_print_entry_obj_default.can_be_blueprint,
            "engram_class_name": engram.get_class().get_name(),
            "required_level": engram.required_character_level,
            "required_engram_points": engram.required_engram_points,
            "stack_size": blue_print_entry_obj_default.max_item_quantity,
        }
        self.builder.add_engram(engram_data)

    def dump(self):
        """Call the builder dump function"""
        self.builder.dump()


def run():
    """Run the parser"""
    unreal_parser = UnrealParser()
    mda_asset_path = unreal_parser.find_mda()
    if mda_asset_path:
        print("Found ModDataAsset_BP asset:", mda_asset_path)
        builder = Builder(BeaconBuilder())
        engram_entries = unreal_parser.get_additional_engram_blueprint_classes(
            mda_asset_path
        )
        for engram in engram_entries:
            # pylint: disable=no-member
            engram_obj = unreal.load_object(None, engram.get_path_name())
            # pylint: disable=no-member
            engram_obj_default = unreal.get_default_object(engram_obj)

            builder.add_engram(engram_obj_default)
        builder.dump()
    else:
        print("ModDataAsset_BP asset not found.")


run()
