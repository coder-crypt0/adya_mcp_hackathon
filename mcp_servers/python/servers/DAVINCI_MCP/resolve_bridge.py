
# Final resolve_bridge_full.py (runs inside Resolve scripting console)

resolve = app.GetResolve()
if resolve is None:
    raise RuntimeError("app.GetResolve() returned None (no Resolve instance found)")
print("[Bridge] Connected to DaVinci Resolve:", resolve.GetVersion())

import socket
import json

pm = resolve.GetProjectManager()
if pm is None:
    raise RuntimeError("resolve.GetProjectManager() returned None (no Project Manager)")

HOST = "127.0.0.1"
PORT = 6060

def safe_get_current_project():
    project = pm.GetCurrentProject()
    if not project:
        raise Exception("No project open.")
    return project

def safe_get_timeline():
    project = safe_get_current_project()
    timeline = project.GetCurrentTimeline()
    if not timeline:
        raise Exception("No timeline open.")
    return timeline

print(f"[Bridge] Listening on {HOST}:{PORT}")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, _ = s.accept()
    with conn:
        while True:
            data = conn.recv(16384)
            if not data:
                break
            try:
                request = json.loads(data.decode())
                action = request["action"]
                args = request.get("args", {})
                result = None

                print(f"[Bridge] Action: {action} | Args: {args}")

                if action == "get_project_list":
                    pm = resolve.GetProjectManager()
                    if pm is None:
                        raise RuntimeError("resolve.GetProjectManager() returned None — make sure a project is open")
                    result = pm.GetProjectList()

                elif action == "open_project":
                    result = pm.LoadProject(args["project_name"])

                elif action == "create_project":
                    result = pm.CreateProject(args["project_name"])

                elif action == "delete_project":
                    result = pm.DeleteProject(args["project_name"])

                elif action == "get_current_project_name":
                    proj = pm.GetCurrentProject()
                    result = proj.GetName() if proj else None

                elif action == "list_timelines":
                    proj = safe_get_current_project()
                    count = proj.GetTimelineCount()
                    result = [proj.GetTimelineByIndex(i+1).GetName() for i in range(count)]

                elif action == "create_timeline":
                    result = safe_get_current_project().CreateTimeline(args["timeline_name"])

                elif action == "delete_timeline":
                    proj = safe_get_current_project()
                    for i in range(proj.GetTimelineCount()):
                        tl = proj.GetTimelineByIndex(i+1)
                        if tl.GetName() == args["timeline_name"]:
                            result = proj.DeleteTimeline(tl)

                elif action == "import_media":
                    mp = safe_get_current_project().GetMediaPool()
                    result = mp.ImportMedia(args["file_paths"])

                elif action == "list_media_pool_items":
                    root = safe_get_current_project().GetMediaPool().GetRootFolder()
                    result = [clip.GetName() for clip in root.GetClipList()]

                elif action == "delete_media_pool_item":
                    root = safe_get_current_project().GetMediaPool().GetRootFolder()
                    for clip in root.GetClipList():
                        if clip.GetName() == args["item_name"]:
                            result = safe_get_current_project().GetMediaPool().DeleteClips([clip])

                elif action == "add_timeline_marker":
                    safe_get_timeline().AddMarker(args["frame_id"], args["color"], args.get("name", ""), args.get("note", ""), 1)
                    result = "Marker added"

                elif action == "list_timeline_markers":
                    result = safe_get_timeline().GetMarkers()

                elif action == "delete_timeline_marker":
                    safe_get_timeline().DeleteMarker(args["frame_id"])
                    result = "Marker deleted"

                elif action == "start_render_job":
                    proj = safe_get_current_project()
                    proj.SetCurrentRenderFormatAndCodec(args["render_preset"], "")
                    job_id = proj.AddRenderJob()
                    proj.StartRendering()
                    result = job_id

                elif action == "list_render_jobs":
                    result = safe_get_current_project().GetRenderJobList()

                elif action == "stop_rendering":
                    safe_get_current_project().StopRendering()
                    result = "Stopped rendering"

                elif action == "export_timeline":
                    result = safe_get_current_project().ExportTimeline(args["file_path"])

                elif action == "apply_lut":
                    result = f"LUT '{args['lut_path']}' applied (simulated)"

                elif action == "run_fusion_script":
                    result = f"Fusion script '{args['script_path']}' executed (simulated)"

                elif action == "batch_project_export":
                    exported = []
                    for name in pm.GetProjectList():
                        pm.LoadProject(name)
                        proj = pm.GetCurrentProject()
                        if proj:
                            path = f"{args['folder_path']}/{name}.drp"
                            proj.ExportProject(path)
                            exported.append(path)
                    result = exported

                else:
                    raise Exception("Unknown action")

                conn.sendall(json.dumps({"result": result}).encode())

            except Exception as e:
                print(f"[Bridge Error] {e}")
                conn.sendall(json.dumps({"error": str(e)}).encode())
