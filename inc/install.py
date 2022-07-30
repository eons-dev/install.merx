import os
import logging
import shutil
from pathlib import Path
from emi import Merx, Epitome

class install(Merx):
    def __init__(this, name="Install"):
        super().__init__(name)

        this.transactionSucceeded = True
        this.rollbackSucceeded = True

    # Required Merx method. See that class for details.
    def Transaction(this):
        for tome in this.tomes:
            logging.info(f"Installing {tome}...")
            epitome = this.GetTome(tome)
            
            if (epitome.installed_at is not None and len(epitome.installed_at)):
                logging.debug(f"Skipping installation for {tome}; it appears to be installed.")
                continue
            
            if (epitome.path is None):
                logging.error(f"Could not find files for {tome}.")
                continue
            
            installedObjects = []

            #assume this.paths are all valid.
            for target, destination in this.paths.items():
                candidate = epitome.path.joinpath(target)
                if (not candidate.exists()):
                    continue

                logging.debug(f"Copying files from {candidate} to {destination}")
                for thing in candidate.iterdir():
                    expectedResult = Path(destination).joinpath(thing.relative_to(candidate)).resolve()
                    installedObjects.append(str(expectedResult))
                    thing = thing.resolve()

                    if (thing.is_dir()):
                        try:
                            shutil.copytree(str(thing), destination)
                            logging.debug(f"Copied {str(thing)}.")
                        except shutil.Error as exc:
                            errors = exc.args[0]
                            for error in errors:
                                src, dst, msg = error
                                logging.debug(f"{msg}")
                    else: #thing is file
                        try:
                            shutil.copy(str(thing), destination)
                            logging.debug(f"Copied {str(thing)}.")
                        except shutil.Error as exc:
                            errors = exc.args[0]
                            for error in errors:
                                src, dst, msg = error
                                logging.debug(f"{msg}")

                    if (not expectedResult.exists()):
                        logging.error(f"COULD NOT FIND {str(expectedResult)}! Will rollback.")
                        this.transactionSucceeded = False
                    logging.debug(f"Created {str(expectedResult)}.")


            epitome.installed_at = ";".join(installedObjects)
            this.catalog.add(epitome)

    # Required Merx method. See that class for details.
    def DidTransactionSucceed(this):
        return this.transactionSucceeded

    # Required Merx method. See that class for details.
    def Rollback(this):
        for tome in this.tomes:
            logging.info(f"Rolling back changes for {tome}...")
            epitome = this.GetTome(tome)
            if (epitome is None):
                logging.error(f"UNABLE TO FIND EPITOME FOR {tome}! SYSTEM STATE UNKNOWN!!!")
                this.rollbackSucceeded = False
                #Uh oh... let's keep going and try to do what we can..
                continue

            toRemove = epitome.installed_at.split(';')
            for thing in toRemove:
                logging.debug(f"REMOVING: {thing}!")
                thing = Path(thing)
                if (not thing.exists()):
                    logging.debug(f"Could not find {str(thing)}.")
                    #That's okay. that might be why we're rolling back ;)
                    continue
                if (thing.is_dir()):
                    thing.rmdir()
                else:
                    thing.unlink()
                logging.debug(f"Removed {str(thing)}.")

        super().Rollback()

    # Required Merx method. See that class for details.
    def DidRollbackSucceed(this):
        return this.rollbackSucceeded