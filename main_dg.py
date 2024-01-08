import os
import numpy as np
import time
from module.ExifData import *
from module.EoData import *
from module.Boundary import boundary
from module.BackprojectionResample import rectify_plane_parallel, createGeoTiff
from rich.console import Console
from rich.table import Table

def orthophoto_process(input_folder, ground_height, sensor_width, epsg, gsd, output_folder_path):
    console = Console()

    if not os.path.exists(output_folder_path):
        os.mkdir(output_folder_path)

    results = []

    for root, dirs, files in os.walk(input_folder):
        files.sort()
        for file in files:
            image_start_time = time.time()
            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1].lower()
            file_path = os.path.join(root, file)
            # dst = os.path.join(output_folder, filename + ".tif")
            dst = os.path.join(output_folder_path, filename)

            if extension == '.jpg':
                print('Georeferencing - ' + file)
                start_time = time.time()
                image = cv2.imread(file_path, -1)

                # 1. Extract metadata from the image
                focal_length, orientation, eo, maker = get_metadata(file_path)
                restored_image = restoreOrientation(image, orientation)

                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # Convert from mm to m
                pixel_size /= 1000

                eo = geographic2plane(eo, epsg)
                opk = rpy_to_opk(eo[3:], maker)
                eo[3:] = opk * np.pi / 180
                R = Rot3D(eo)

                georef_time = time.time() - start_time

                # 2. Compute DEM & GSD
                print('DEM & GSD')
                start_time = time.time()
                bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)
                
                if gsd == 0:
                    gsd = (pixel_size * (eo[2] - ground_height)) / focal_length
                
                boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

                dem_time = time.time() - start_time

                # 3. Rectify & Resample
                print('Rectify & Resampling')
                start_time = time.time()
                b, g, r, a = rectify_plane_parallel(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height,
                                                    R, focal_length, pixel_size, image)
                rectify_time = time.time() - start_time

                # 4. Create GeoTiff
                print('Save the image in GeoTiff')
                start_time = time.time()
                createGeoTiff(b, g, r, a, bbox, gsd, epsg, boundary_rows, boundary_cols, dst)
                write_time = time.time() - start_time

                processing_time = time.time() - image_start_time

                results.append({
                    "filename": filename,
                    "georef_time": round(georef_time, 5),
                    "dem_time": round(dem_time, 5),
                    "rectify_time": round(rectify_time, 5),
                    "write_time": round(write_time, 5),
                    "processing_time": round(processing_time, 5)
                })

    # Display results in a table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Image", style="dim", width=12)
    table.add_column("Georeferencing", justify="right")
    table.add_column("DEM", justify="right")
    table.add_column("Rectify", justify="right")
    table.add_column("Write", justify="right")
    table.add_column("Processing", justify="right")

    for result in results:
        table.add_row(
            result["filename"],
            str(result["georef_time"]),
            str(result["dem_time"]),
            str(result["rectify_time"]),
            str(result["write_time"]),
            str(result["processing_time"])
        )

    console.print(table)

    return output_folder_path

def orthophoto_process_single_image(image_path, ground_height, sensor_width, epsg, gsd, output_folder_path):
    console = Console()
    
    # Check if output_folder_path exists, if not, create it
    if not os.path.exists(output_folder_path):
        os.mkdir(output_folder_path)

    results = []

    filename = os.path.splitext(os.path.basename(image_path))[0]
    dst = os.path.join(output_folder_path, filename)
    
    print('Georeferencing - ' + image_path)
    image_start_time = time.time()
    image = cv2.imread(image_path, -1)

    # 1. Extract metadata from the image
    start_time = time.time()
    focal_length, orientation, eo, maker = get_metadata(image_path)
    restored_image = restoreOrientation(image, orientation)

    image_rows = restored_image.shape[0]
    image_cols = restored_image.shape[1]

    pixel_size = sensor_width / image_cols  # Convert from mm to m
    pixel_size /= 1000

    eo = geographic2plane(eo, epsg)
    opk = rpy_to_opk(eo[3:], maker)
    eo[3:] = opk * np.pi / 180
    R = Rot3D(eo)

    georef_time = time.time() - start_time

    # 2. Compute DEM & GSD
    print('DEM & GSD')
    start_time = time.time()
    bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)
    
    if gsd == 0:
        gsd = (pixel_size * (eo[2] - ground_height)) / focal_length
    
    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
    boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

    dem_time = time.time() - start_time

    # 3. Rectify & Resample
    print('Rectify & Resampling')
    start_time = time.time()
    b, g, r, a = rectify_plane_parallel(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height,
                                        R, focal_length, pixel_size, image)
    rectify_time = time.time() - start_time

    # 4. Create GeoTiff
    print('Save the image in GeoTiff')
    start_time = time.time()

    createGeoTiff(b, g, r, a, bbox, gsd, epsg, boundary_rows, boundary_cols, dst)

    write_time = time.time() - start_time

    processing_time = time.time() - image_start_time

    results.append({
        "filename": filename,
        "georef_time": round(georef_time, 5),
        "dem_time": round(dem_time, 5),
        "rectify_time": round(rectify_time, 5),
        "write_time": round(write_time, 5),
        "processing_time": round(processing_time, 5)
    })

    # Display results in a table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Image", style="dim", width=12)
    table.add_column("Georeferencing", justify="right")
    table.add_column("DEM", justify="right")
    table.add_column("Rectify", justify="right")
    table.add_column("Write", justify="right")
    table.add_column("Processing", justify="right")

    for result in results:
        table.add_row(
            result["filename"],
            str(result["georef_time"]),
            str(result["dem_time"]),
            str(result["rectify_time"]),
            str(result["write_time"]),
            str(result["processing_time"])
        )

    console.print(table)
    
    return dst

def rot_2d(theta):
    return np.array([[np.cos(theta), np.sin(theta)],
                     [-np.sin(theta), np.cos(theta)]])

def rpy_to_opk(rpy, tag="DJI"):
    roll_pitch = np.empty_like(rpy[0:2])
    if tag == "DJI":
        roll_pitch[0] = 90 + rpy[1]
        if 180 - abs(rpy[0]) <= 0.1:
            roll_pitch[1] = 0
        else:
            roll_pitch[1] = rpy[0]

        omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
        kappa = -rpy[2]
        return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])
    elif tag == "SUNLIGHT":
        roll_pitch[0] = -rpy[1]
        roll_pitch[1] = -rpy[0]

        omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
        kappa = -rpy[2] + 90
        return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])
    elif tag == "VTOL":
        roll_pitch[0] = -rpy[0]
        roll_pitch[1] = rpy[1]

        omega_phi = np.dot(rot_2d(rpy[2] * np.pi / 180), roll_pitch.reshape(2, 1))
        kappa = -rpy[2] - 90
        return np.array([float(omega_phi[0, 0]), float(omega_phi[1, 0]), kappa])
    else:
        raise Exception(" * An invalid type of hostname!!! Not DJI/SUNLIGHT/VTOL")

def orthophoto_process_custom_input(image_path, longitude, latitude, altitude, focal_length_input, roll, pitch, yaw, 
                                    ground_height, sensor_width, epsg, gsd, output_folder_path, tag="DJI"):
    console = Console()

    if not os.path.exists(output_folder_path):
        os.mkdir(output_folder_path)

    results = []

    filename = os.path.splitext(os.path.basename(image_path))[0]
    dst = os.path.join(output_folder_path, filename)
    
    print('Georeferencing - ' + image_path)
    image_start_time = time.time()
    image = cv2.imread(image_path, -1)

    omega, phi, kappa = rpy_to_opk(np.array([roll, pitch, yaw]), tag)

    eo = np.array([longitude, latitude, altitude, omega, phi, kappa])
    eo[3:] *= np.pi / 180
    R = Rot3D(eo)

    image_rows = image.shape[0]
    image_cols = image.shape[1]
    pixel_size = sensor_width / image_cols  # Convert from mm to m
    pixel_size /= 1000

    georef_time = time.time() - image_start_time

    print('DEM & GSD')
    start_time = time.time()
    bbox = boundary(image, eo, R, ground_height, pixel_size, focal_length_input)
    if gsd == 0:
        gsd = (pixel_size * (eo[2] - ground_height)) / focal_length_input
    boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
    boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)
    dem_time = time.time() - start_time

    print('Rectify & Resampling')
    start_time = time.time()
    b, g, r, a = rectify_plane_parallel(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height, R, focal_length_input, pixel_size, image)
    rectify_time = time.time() - start_time
    print(f"Destination: {dst}")
    print(f"Rows: {boundary_rows}, Cols: {boundary_cols}")
    print('Save the image in GeoTiff')
    print(f"bbox: {bbox}, gsd: {gsd}, epsg: {epsg}")
    start_time = time.time()
    createGeoTiff(b, g, r, a, bbox, gsd, epsg, boundary_rows, boundary_cols, dst)

    write_time = time.time() - start_time

    processing_time = time.time() - image_start_time
    results.append({
        "filename": filename,
        "georef_time": round(georef_time, 5),
        "dem_time": round(dem_time, 5),
        "rectify_time": round(rectify_time, 5),
        "write_time": round(write_time, 5),
        "processing_time": round(processing_time, 5)
    })

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Image", style="dim", width=12)
    table.add_column("Georeferencing", justify="right")
    table.add_column("DEM", justify="right")
    table.add_column("Rectify", justify="right")
    table.add_column("Write", justify="right")
    table.add_column("Processing", justify="right")

    for result in results:
        table.add_row(
            result["filename"],
            str(result["georef_time"]),
            str(result["dem_time"]),
            str(result["rectify_time"]),
            str(result["write_time"]),
            str(result["processing_time"])
        )

    console.print(table)
    return dst
