from fastapi import FastAPI, Query, HTTPException, UploadFile, File, status
from fastapi import Depends
from main_dg import orthophoto_process, orthophoto_process_single_image, orthophoto_process_custom_input
from fastapi.responses import FileResponse, RedirectResponse
import uvicorn
import os
import zipfile
import uuid
from enum import Enum


class DroneType(str, Enum):
    DJI_MAVIC_Pro_Platinum = "DJI_Mavic_Pro_Platinum"
    DJI_PHANTOM_4 = "DJI_Phantom_4"
    DJI_ZENMUSE_M300_P1 = "DJI_M300_Zenmuse_P1"
    # SUNLIGHT = "Sunlight"
    VTOL_HALLA_AR0234 = "VTOL_Halla_AR0234"
    VTOL_HALLA_B0240 = "VTOL_Halla_B0240"

class DroneType_input_type(str, Enum):
    DJI_MAVIC_Pro_Platinum = "DJI_Mavic_Pro_Platinum"
    DJI_PHANTOM_4 = "DJI_Phantom_4"
    DJI_ZENMUSE_M300_P1_fc_24 = "DJI_M300_Zenmuse_P1_fc_24"
    DJI_ZENMUSE_M300_P1_fc_35 = "DJI_M300_Zenmuse_P1_fc_35"
    DJI_ZENMUSE_M300_P1_fc_50 = "DJI_M300_Zenmuse_P1_fc_50"
    # SUNLIGHT = "Sunlight"
    VTOL_HALLA_AR0234 = "VTOL_Halla_AR0234"
    VTOL_HALLA_B0240 = "VTOL_Halla_B0240"

class DroneTag(str, Enum):
    DJI = "DJI"
    SUNLIGHT = "SUNLIGHT"
    VTOL = "VTOL"

DEFAULT_PARAMS = {
    DroneType.DJI_MAVIC_Pro_Platinum: {"ground_height": 0, "sensor_width": 6.16, "epsg": 5186, "gsd": 0},
    DroneType.DJI_PHANTOM_4: {"ground_height": 0, "sensor_width": 13.2, "epsg": 5186, "gsd": 0},
    DroneType.DJI_ZENMUSE_M300_P1: {"ground_height": 0, "sensor_width": 15.9, "epsg": 5186, "gsd": 0},
    # DroneType.SUNLIGHT: {"ground_height": 0, "sensor_width": 0, "epsg": 5186, "gsd": 0},
    DroneType.VTOL_HALLA_AR0234: {"ground_height": 0, "sensor_width": 5.76, "epsg": 5186, "gsd": 0},
    DroneType.VTOL_HALLA_B0240: {"ground_height": 0, "sensor_width": 6.287, "epsg": 5186, "gsd": 0},
}

DEFAULT_PARAMS_input_type = {
    DroneType_input_type.DJI_MAVIC_Pro_Platinum: {"ground_height": 0, "sensor_width": 6.16, "epsg": 5186, "gsd": 0, "focal_length": 4.98},
    DroneType_input_type.DJI_PHANTOM_4: {"ground_height": 0, "sensor_width": 13.2, "epsg": 5186, "gsd": 0, "focal_length": 8.8},
    DroneType_input_type.DJI_ZENMUSE_M300_P1_fc_24: {"ground_height": 0, "sensor_width": 15.9, "epsg": 5186, "gsd": 0, "focal_length": 24},
    DroneType_input_type.DJI_ZENMUSE_M300_P1_fc_35: {"ground_height": 0, "sensor_width": 15.9, "epsg": 5186, "gsd": 0, "focal_length": 35},
    DroneType_input_type.DJI_ZENMUSE_M300_P1_fc_50: {"ground_height": 0, "sensor_width": 15.9, "epsg": 5186, "gsd": 0, "focal_length": 50},
    # DroneType.SUNLIGHT: {"ground_height": 0, "sensor_width": 0, "epsg": 5186, "gsd": 0, "focal_length": 5.0},
    DroneType_input_type.VTOL_HALLA_AR0234: {"ground_height": 0, "sensor_width": 5.76, "epsg": 5186, "gsd": 0, "focal_length": 3.6},
    DroneType_input_type.VTOL_HALLA_B0240: {"ground_height": 0, "sensor_width": 6.287, "epsg": 5186, "gsd": 0, "focal_length": 6},
}

DRONE_TYPE_TO_TAG_MAP = {
    DroneType_input_type.DJI_MAVIC_Pro_Platinum: DroneTag.DJI,
    DroneType_input_type.DJI_PHANTOM_4: DroneTag.DJI,
    DroneType_input_type.DJI_ZENMUSE_M300_P1_fc_24: DroneTag.DJI,
    DroneType_input_type.DJI_ZENMUSE_M300_P1_fc_35: DroneTag.DJI,
    DroneType_input_type.DJI_ZENMUSE_M300_P1_fc_50: DroneTag.DJI,
    DroneType_input_type.VTOL_HALLA_AR0234: DroneTag.VTOL,
    DroneType_input_type.VTOL_HALLA_B0240: DroneTag.VTOL
}


def custom_drone_params(drone_type: DroneType = Query(...),
                        ground_height: float = Query(0, description="Ground height in meters / unit: m"),
                        epsg: int = Query(5186, description="EPSG code for the geographic coordinate system / editable"),
                        gsd: float = Query(0, description="Ground Sampling Distance in meters")):
    return {
        "ground_height": ground_height if ground_height is not None else DEFAULT_PARAMS[drone_type]["ground_height"],
        "sensor_width": DEFAULT_PARAMS[drone_type]["sensor_width"],  # This will always use the default value
        "epsg": epsg if epsg is not None else DEFAULT_PARAMS[drone_type]["epsg"],
        "gsd": gsd if gsd is not None else DEFAULT_PARAMS[drone_type]["gsd"]
    }

def custom_drone_params_single_image(drone_type: DroneType = Query(...),
                        ground_height: float = Query(0, description="Ground height in meters / unit: m"),
                        epsg: int = Query(5186, description="EPSG code for the geographic coordinate system / editable"),
                        gsd: float = Query(0, description="Ground Sampling Distance in meters")):
    return {
        "ground_height": ground_height if ground_height is not None else DEFAULT_PARAMS[drone_type]["ground_height"],
        "sensor_width": DEFAULT_PARAMS[drone_type]["sensor_width"],  # This will always use the default value
        "epsg": epsg if epsg is not None else DEFAULT_PARAMS[drone_type]["epsg"],
        "gsd": gsd if gsd is not None else DEFAULT_PARAMS[drone_type]["gsd"]
    }

app = FastAPI()

@app.post("/Orthophoto/", tags=["Metadata - Datasets format - zip format"])
async def Input_datasets_format(
    drone_type: DroneType,
    params: dict = Depends(custom_drone_params),
    zip_file: UploadFile = File(...)):
    return await process_datasets(params, zip_file)

@app.post("/Orthophoto/custom/", tags=["Metadata - Datasets format - zip format"])
async def Input_datasets_custom_format(
    zip_file: UploadFile = File(...),
    ground_height: float = Query(0, description="Ground height in meters / unit: m"),
    sensor_width: float = Query(6.3, description="Sensor width in millimeters / unit: mm, Mavic"),
    epsg: int = Query(5186, description="EPSG code for the geographic coordinate system / editable"),
    gsd: float = Query(0, description="Ground Sampling Distance in meters")):

    params = {
        "ground_height": ground_height,
        "sensor_width": sensor_width,
        "epsg": epsg,
        "gsd": gsd
    }

    return await process_datasets(params, zip_file)

async def process_datasets(params: dict, zip_file: UploadFile):
    ground_height = params.get("ground_height")
    sensor_width = params.get("sensor_width")
    epsg = params.get("epsg")
    gsd = params.get("gsd")

    # Use default parameters based on drone type if specific values are not provided
    ground_height = ground_height if ground_height is not None else DEFAULT_PARAMS[drone_type]["ground_height"]
    sensor_width = sensor_width if sensor_width is not None else DEFAULT_PARAMS[drone_type]["sensor_width"]
    epsg = epsg if epsg is not None else DEFAULT_PARAMS[drone_type]["epsg"]
    gsd = gsd if gsd is not None else DEFAULT_PARAMS[drone_type]["gsd"]
    zip_location = "/data/temp_upload.zip"
    
    with open(zip_location, "wb") as buffer:
        buffer.write(zip_file.file.read())

    extraction_folder = "/data/extracted_files"
    with zipfile.ZipFile(zip_location, 'r') as zip_ref:
        zip_ref.extractall(extraction_folder)

    # Generate a unique output folder path
    unique_output_id = str(uuid.uuid4())
    output_folder_path = os.path.join("/data/outputs", unique_output_id)

    # Ensure the directory exists
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    output_folder = orthophoto_process(extraction_folder, ground_height, sensor_width, epsg, gsd, output_folder_path)
    
    zip_output_name = os.path.join("/data", f"{unique_output_id}.zip")
    with zipfile.ZipFile(zip_output_name, 'w') as zipf:
        for foldername, subfolders, filenames in os.walk(output_folder):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                zipf.write(file_path, os.path.basename(file_path))

    return RedirectResponse(url=f"/download/{unique_output_id}", status_code=status.HTTP_302_FOUND)
    
@app.get("/download/{unique_id}", include_in_schema=False)
async def download_files(unique_id: str):
    return FileResponse(f"/data/{unique_id}.zip", filename=f"{unique_id}.zip")

@app.post("/Orthophoto//", tags=["Metadata format - Single image"])
async def Input_single_image_default(
    drone_type: DroneType,
    params: dict = Depends(custom_drone_params_single_image),
    image: UploadFile = File(...)):

    return await process_single_image(params, image)

@app.post("/Orthophoto//custom/", tags=["Metadata format - Single image"])
async def Input_single_image_custom(
    image: UploadFile = File(...),
    ground_height: float = Query(0, description="Ground height in meters / unit: m"),
    sensor_width: float = Query(6.3, description="Sensor width in millimeters / unit: mm, Mavic"),
    epsg: int = Query(5186, description="EPSG code for the geographic coordinate system / editable"),
    gsd: float = Query(0, description="Ground Sampling Distance in meters")):

    params = {
        "ground_height": ground_height,
        "sensor_width": sensor_width,
        "epsg": epsg,
        "gsd": gsd
    }

    return await process_single_image(params, image)

async def process_single_image(params: dict, image: UploadFile):
    image_location = f"/data/{image.filename}"
    with open(image_location, "wb") as buffer:
        buffer.write(image.file.read())

    output_folder_path = "/data/outputs_single"
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    output_image_path = orthophoto_process_single_image(image_location, 
                                                        params['ground_height'],
                                                        params['sensor_width'], 
                                                        params['epsg'], 
                                                        params['gsd'], 
                                                        output_folder_path)

    unique_image_name = os.path.basename(output_image_path)
    if not unique_image_name.endswith('.tif'):
        unique_image_name += '.tif'
    
    download_url = f"/download_image/{unique_image_name}"
    return RedirectResponse(url=download_url, status_code=status.HTTP_302_FOUND)

@app.get("/download_image/{filename}", include_in_schema=False)
async def download_image(filename: str):
    return FileResponse(os.path.join("/data/outputs_single", filename), filename=filename)

@app.post("/Orthophoto/SingleImageInput/", tags=["Input Type format - Single image"])
async def input_single_image_with_input(
    drone_type: DroneType_input_type,
    image: UploadFile = File(..., description="The aerial image to be processed."),
    ground_height: float = Query(0, description="unit: m"),
    epsg: int = Query(5186, description="EPSG. / Default is 5186."),
    gsd: float = Query(0, description="GSD in meters. If set to 0, it will be automatically calculated based on other input parameters. / Unit: m"),
    longitude: float = Query(..., description="Unit: degrees"),
    latitude: float = Query(..., description="Unit: degrees"),
    altitude: float = Query(..., description="Unit: m"),
    roll: float = Query(..., description="Unit: degrees"),
    pitch: float = Query(..., description="Unit: degrees"),
    yaw: float = Query(..., description="Unit: degrees")
):

    sensor_width = DEFAULT_PARAMS_input_type[drone_type]["sensor_width"]
    # focal_length = DEFAULT_PARAMS_input_type[drone_type]["focal_length"]
    focal_length_mm = DEFAULT_PARAMS_input_type[drone_type]["focal_length"]
    focal_length = round(focal_length_mm / 1000, 2)
    tag = DRONE_TYPE_TO_TAG_MAP[drone_type]

    params = {
        "ground_height": ground_height,
        "sensor_width": sensor_width,
        "epsg": epsg,
        "gsd": gsd,
        "longitude": longitude,
        "latitude": latitude,
        "altitude": altitude,
        "focal_length": focal_length,
        "roll": roll,
        "pitch": pitch,
        "yaw": yaw,
        "tag": tag
    }

    return await process_single_image_with_custom_input(params, image)

async def process_single_image_with_custom_input(params: dict, image: UploadFile):
    image_location = f"/data/{image.filename}"
    
    if not os.path.exists(os.path.dirname(image_location)):
        os.makedirs(os.path.dirname(image_location))

    with open(image_location, "wb") as buffer:
        buffer.write(image.file.read())

    output_folder_path = "/data/outputs_single"
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    try:
        output_image_path = orthophoto_process_custom_input(image_location, 
                                                            params['longitude'],
                                                            params['latitude'],
                                                            params['altitude'],
                                                            params['focal_length'],
                                                            params['roll'],
                                                            params['pitch'],
                                                            params['yaw'],
                                                            params['ground_height'],
                                                            params['sensor_width'], 
                                                            params['epsg'], 
                                                            params['gsd'], 
                                                            output_folder_path,
                                                            tag=params["tag"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

    unique_image_name = os.path.basename(output_image_path)
    if not unique_image_name.endswith('.tif'):
        unique_image_name += '.tif'
    
    download_url = f"/download_image/{unique_image_name}"
    return RedirectResponse(url=download_url, status_code=status.HTTP_302_FOUND)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)