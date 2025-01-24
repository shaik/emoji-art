import json
import os
from datetime import datetime

class BuildManager:
    BUILD_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'build.json')

    @classmethod
    def get_build_info(cls):
        if not os.path.exists(cls.BUILD_FILE):
            return {"build_number": 1, "last_updated": datetime.now().isoformat()}
        
        try:
            with open(cls.BUILD_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"build_number": 1, "last_updated": datetime.now().isoformat()}

    @classmethod
    def increment_build(cls):
        build_info = cls.get_build_info()
        build_info["build_number"] += 1
        build_info["last_updated"] = datetime.now().isoformat()
        
        with open(cls.BUILD_FILE, 'w') as f:
            json.dump(build_info, f, indent=4)
        
        return build_info
