"""A parser for UE5 ARK SA DevKit that extracts data from your mod"""

import argparse
import tempfile
import tarfile
import shutil
import uuid
import time
import json
import csv
import os
import unreal

BEACON_NAMESPACE = uuid.UUID("82aa4465-85f9-4b9e-8d36-f66164cef0a6")
BASE_CONTENT_PACK_ID = "b32a3d73-9406-56f2-bd8f-936ee0275249"


class MissingDataException(Exception):
    """Raised when crucial data is missing"""

    def __init__(self, message):
        super().__init__(message)


class MissingArgumentException(Exception):
    """Raised when crucial arguments is missing"""

    def __init__(self, message):
        super().__init__(message)


class Utils:
    """A class with some helpful utilities"""

    @classmethod
    def make_tmp_dir(cls):
        """Creates and returns a temporary directory"""
        tmp_dir = tempfile.mkdtemp()
        return tmp_dir

    @classmethod
    def remove_tmp_dir(cls, tmp_dir):
        """Removes a previously created temporary directory"""
        shutil.rmtree(tmp_dir)

    @classmethod
    def dump_to_file(cls, tmp_dir, file_name, contents):
        """Dumps data to a file given a directory, a file name, and its contents"""
        with open(os.path.join(tmp_dir, file_name), "w", encoding="utf-8") as text_file:
            text_file.write(contents)

    @classmethod
    def is_valid_directory(cls, path):
        """Checks that a given directory is valid"""
        if not os.path.isdir(path):
            raise argparse.ArgumentTypeError(f"{path} is not a valid directory")
        return path

    @classmethod
    def create_beacondata(cls, folder_path, output_path):
        """Create the beacondata file"""
        with tarfile.open(output_path, "w:gz") as tar:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    tar.add(file_path, arcname=os.path.relpath(file_path, folder_path))


class EngramEntry:
    """A parser class for engram entries"""

    def __init__(self, engram):
        self.engram_data = {}
        self.parse_engram(engram)

    def parse_engram(self, engram):
        """Parse the engram"""
        self.engram_data = {
            "engram_class_name": engram.get_class().get_name(),
            "required_level": engram.required_character_level,
            "required_engram_points": engram.required_engram_points,
        }

    def __getitem__(self, key):
        """Allow indexing to access items in engram_data"""
        return self.engram_data[key]


class PrimalItem:
    """A parser class for primal items"""

    def __init__(self, primal_item):
        self.primal_item_data = {}
        # pylint: disable=no-member
        primal_item_obj_default = unreal.get_default_object(primal_item)
        self.parse_primal_item(primal_item, primal_item_obj_default)

    def parse_primal_item(self, primal_item, primal_item_obj_default):
        """Parse the primal item data into a dictionary"""
        primal_item_path = primal_item.get_path_name()[:-2]
        self.primal_item_data = {
            "primal_item_path": primal_item_path,
            "primal_item_name": primal_item_obj_default.descriptive_name_base,
            "blueprintable": primal_item_obj_default.can_be_blueprint,
            "stack_size": primal_item_obj_default.max_item_quantity,
            "crafting_requirements": primal_item_obj_default.base_crafting_resource_requirements,
        }

    def __getitem__(self, key):
        """Allow indexing to access items in primal_item_data"""
        return self.primal_item_data[key]


class BeaconBuilder:
    """A builder class that creates files in a format that can be imported into Beacon"""

    def __init__(self, mod_parser):
        self.mod_parser = mod_parser
        self.engrams = []
        self.output_file_path = ""

    def add_engram(self, engram, primal_item):
        """Adds an engram to the engrams array"""
        tags = []
        if primal_item["blueprintable"]:
            tags.append("blueprintable")
        engram = {
            "group": "engrams",
            "engramId": self.mod_parser.uuid_from_path(primal_item["primal_item_path"]),
            "label": primal_item["primal_item_name"],
            "alternateLabel": None,
            "tags": tags,
            "availability": 3,
            "path": primal_item["primal_item_path"],
            "minVersion": 20000000,
            "lastUpdate": time.time(),
            "contentPackId": self.mod_parser.mod_data["content_pack_id"],
            "contentPackName": self.mod_parser.mod_data["mod_name"],
            "entryString": engram["engram_class_name"],
            "requiredLevel": engram["required_level"],
            "requiredPoints": engram["required_engram_points"],
            "stackSize": primal_item["stack_size"],
        }

        recipe = []
        crafting_requirements = primal_item["crafting_requirements"]
        for crafting_requirement in crafting_requirements:
            requirements = {
                "engramId": self.mod_parser.uuid_from_path(crafting_requirement.resource_item_type.get_path_name()[:-2]),
                "quantity": int(crafting_requirement.base_resource_requirement),
                "exact": crafting_requirement.crafting_require_exact_resource_type,
            }
            recipe.append(requirements)
        engram["recipe"] = recipe

        self.engrams.append(engram)

    def build(self, tmp_dir):
        """Build the contents of the json file that Beacon uses"""
        content_pack = [
            {
                "contentPackId": self.mod_parser.mod_data["content_pack_id"],
                "gameId": "ArkSA",
                "marketplace": "CurseForge",
                "marketplaceId": self.mod_parser.mod_data["mod_id"],
                "name": self.mod_parser.mod_data["mod_name"],
                "isConsoleSafe": False,
                "isDefaultEnabled": False,
                "minVersion": 20000000,
                "lastUpdate": time.time(),
            }
        ]
        content_packs = {"gameId": "ArkSA", "contentPacks": content_pack}
        content = {"payloads": [content_packs, {"gameId": "ArkSA", "engrams": self.engrams}]}
        Utils.dump_to_file(
            tmp_dir,
            f"{self.mod_parser.mod_data['content_pack_id']}.json",
            json.dumps(content, indent=4),
        )

    def build_manifest(self, tmp_dir):
        """Build the manifest json file for Beacon"""
        manifest = {
            "version": 7,
            "minVersion": 7,
            "generatedWith": 20100301,
            "isFull": False,
            "files": [f"{self.mod_parser.mod_data['content_pack_id']}.json"],
            "isUserData": True,
        }
        Utils.dump_to_file(tmp_dir, "Manifest.json", json.dumps(manifest, indent=4))

    def dump(self):
        """Dump all of the data to the temp directly and create the beacondata file"""
        temp_dir = Utils.make_tmp_dir()
        self.build(temp_dir)
        self.build_manifest(temp_dir)
        file_name = f"{self.mod_parser.mod_data['mod_name']}.beacondata"
        self.output_file_path = os.path.join(self.mod_parser.output_dir, file_name)
        Utils.create_beacondata(temp_dir, self.output_file_path)
        Utils.remove_tmp_dir(temp_dir)


class StandardBuilder:
    """A standard builder that returns generic json extracted from the mod"""

    def __init__(self, mod_parser):
        self.mod_parser = mod_parser
        self.engrams = []
        self.output_file_path = ""

    def add_engram(self, engram, primal_item):
        """Adds an engram to the engram array"""
        engram = {
            "name": primal_item["primal_item_name"],
            "path": primal_item["primal_item_path"],
            "stackSize": primal_item["stack_size"],
            "entryString": engram["engram_class_name"],
            "requiredLevel": engram["required_level"],
            "requiredPoints": engram["required_engram_points"],
        }

        recipe = []
        crafting_requirements = primal_item["crafting_requirements"]
        for crafting_requirement in crafting_requirements:
            requirements = {
                "friendly_resource_name": PrimalItem(crafting_requirement.resource_item_type)["primal_item_name"],
                "resource": crafting_requirement.resource_item_type.get_path_name()[:-2],
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
        file_name = f"{self.mod_parser.mod_data['mod_name']}-data.json"
        Utils.dump_to_file(
            self.mod_parser.output_dir,
            file_name,
            data,
        )
        self.output_file_path = os.path.join(self.mod_parser.output_dir, file_name)


class CSVBuilder(StandardBuilder):
    """A builder class that creates files in a format that can be imported into Excel/Sheets"""

    def __init__(self, mod_parser):
        super().__init__(mod_parser)
        self.mod_parser = mod_parser
        self.engrams = []
        self.output_file_path = ""

    def dump(self):
        """Dump the csv file"""
        file_name = f"{self.mod_parser.mod_data['mod_name']}.csv"
        self.output_file_path = os.path.join(self.mod_parser.output_dir, file_name)

        fields = ["Item Name", "Item Path", "Max Stack Size", "Engram Class Name", "Required Level", "Required Engram Points", "Crafting Recipe"]
        with open(self.output_file_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(fields)

            for engram in self.engrams:
                name = engram["name"]
                path = engram["path"]
                stack_size = engram["stackSize"]
                entry_string = engram["entryString"]
                required_level = engram["requiredLevel"]
                required_points = engram["requiredPoints"]
                recipe = engram["recipe"]
                recipe_as_list = []
                for ingredient in recipe:
                    resource = ingredient["friendly_resource_name"]
                    quantity = ingredient["quantity"]
                    exact = ingredient["exact"]
                    recipe_as_list.append(f"{resource} x{quantity} (Exact: {exact})")

                # TODO: Add entries for learning the engram, hiding the engram, giving the item, (maybe) modifying crafting recipe?
                writer.writerow([name, path, stack_size, entry_string, required_level, required_points, "\n".join(recipe_as_list)])


class EngramBuilder:
    """Base builder class, allows user to choose which output they prefer"""

    def __init__(self, mod_parser, builder):
        self.mod_parser = mod_parser
        self.builder = builder

    def add_engram(self, engram, primal_item):
        """Call the builders add_engram function"""
        self.builder.add_engram(engram, primal_item)

    def dump(self):
        """Call the builder dump function"""
        self.builder.dump()

    def get_output_file(self):
        """Returns the output file path"""
        return self.builder.output_file_path


class ModParser:
    """Base class for all of the mod parsing"""

    def __init__(self):
        self.output_dir = ""
        self.content_pack_ids = {
            "/Game/": BASE_CONTENT_PACK_ID,
            "/Packs/": BASE_CONTENT_PACK_ID,
        }
        self.mod_data = {}

        self.parse_arguments()

    def uuid_from_path(self, path):
        """Converts a UE5 path into a V5 UUID"""
        for prefix, content_pack_id in self.content_pack_ids.items():
            if path.startswith(prefix):
                return str(uuid.uuid5(BEACON_NAMESPACE, f"{content_pack_id.lower()}:{path.lower()}"))
        return None

    def parse_arguments(self):
        """Parses arguments from CLI"""
        parser = argparse.ArgumentParser(description="Description of your program")

        subparsers = parser.add_subparsers(dest="subcommand", title="Subcommands", description="Choose a subcommand")

        # Beacon subparser, requires more inputs than the standard parser does
        parser_beacon = subparsers.add_parser("beacon", help="Use the Beacon parser to generate a .beacondata file")
        parser_beacon.add_argument("--mod-root-folder", type=str, help="Root folder of the mod")
        parser_beacon.add_argument("--mod-id", type=str, help="ID of the mod")
        parser_beacon.add_argument("--mod-name", type=str, help="Name of the mod")
        parser_beacon.add_argument("--content-pack-id", type=str, help="ID of the content pack")
        parser_beacon.add_argument("--output-folder", type=Utils.is_valid_directory, help="Output folder")
        parser_beacon.add_argument("--mda", type=str, default="ModDataAsset", help="ModDataAsset file name, defaults to ModDataAsset")

        # Standard parser
        parser_standard = subparsers.add_parser("standard", help="Activate standard")
        parser_standard.add_argument("--mod-root-folder", type=str, help="Root folder of the mod")
        parser_standard.add_argument("--output-folder", type=str, help="Output folder")
        parser_standard.add_argument("--mod-name", type=str, help="Name of the mod")
        parser_standard.add_argument("--mda", type=str, default="ModDataAsset", help="ModDataAsset file name, defaults to ModDataAsset")

        # CSV parser
        parser_csv = subparsers.add_parser("csv", help="Activate csv to generate a .csv file")
        parser_csv.add_argument("--mod-root-folder", type=str, help="Root folder of the mod")
        parser_csv.add_argument("--output-folder", type=str, help="Output folder")
        parser_csv.add_argument("--mod-name", type=str, help="Name of the mod")
        parser_csv.add_argument("--mda", type=str, default="ModDataAsset", help="ModDataAsset file name, defaults to ModDataAsset")

        # Parse the args and ensure we got all the ones we need
        args = parser.parse_args()
        missing_args = [arg_name for arg_name, arg_value in vars(args).items() if arg_value is None]
        if missing_args:
            raise MissingArgumentException(f"Not all arguments were provided, missing: {missing_args}")

        # Distribute the args to their relevant places
        subcommand = args.subcommand
        if subcommand == "beacon":
            self.mod_data["content_pack_id"] = args.content_pack_id
            self.mod_data["mod_id"] = args.mod_id
            self.content_pack_ids[args.mod_root_folder] = args.content_pack_id

        self.mod_data["mod_root_folder"] = args.mod_root_folder
        self.mod_data["mod_name"] = args.mod_name
        self.output_dir = args.output_folder
        self.mda_name = args.mda
        self.parser = subcommand

        return args

    def find_mda(self):
        """Find the mod data asset for this mod"""
        # pylint: disable=no-member
        assets = unreal.EditorAssetLibrary.list_assets(self.mod_data["mod_root_folder"], recursive=True)
        for asset_path in assets:
            asset_name = unreal.Paths.get_base_filename(asset_path)
            # Since we ask for the Mod Path in the command, we can be sure this is the correct MDA
            if self.mda_name.lower() in asset_name.lower():
                return asset_path
        raise MissingDataException("Could not find a file with 'ModDataAsset' in it's name in the given mod_root_folder")

    def get_additional_engram_blueprint_classes(self, asset_path):
        """Gets the additional engram blueprint classes field from the mod data asset"""
        # pylint: disable=no-member
        asset_object = unreal.EditorAssetLibrary.load_asset(asset_path)
        if asset_object:
            additional_engram_blueprint_classes = asset_object.additional_engram_blueprint_classes
            if additional_engram_blueprint_classes:
                return additional_engram_blueprint_classes
        else:
            raise MissingDataException(f"Failed to load asset: {asset_path}")
        return None

    def run(self):
        """Run the parser"""
        print("Starting ARK SA Mod Data Parser")
        mda_asset_path = self.find_mda()
        print(f"Found ModDataAsset_BP asset: {mda_asset_path}")
        parsers = {
            "beacon": BeaconBuilder,
            "standard": StandardBuilder,
            "csv": CSVBuilder,
        }
        builder = EngramBuilder(self, parsers[self.parser](mod_parser=self))
        engram_entries = self.get_additional_engram_blueprint_classes(mda_asset_path)
        print(f"{len(engram_entries)} engram entries found.")
        for engram in engram_entries:
            # pylint: disable=no-member
            engram_obj = unreal.load_object(None, engram.get_path_name())
            # pylint: disable=no-member
            engram_obj_default = unreal.get_default_object(engram_obj)
            engram_entry = EngramEntry(engram_obj_default)

            _primal_item = engram_obj_default.blue_print_entry
            # pylint: disable=no-member
            primal_item_obj = unreal.load_object(None, _primal_item.get_path_name())
            primal_item = PrimalItem(primal_item_obj)

            builder.add_engram(engram_entry, primal_item)
        builder.dump()
        print(f"Done! {builder.get_output_file()}")


ModParser().run()
