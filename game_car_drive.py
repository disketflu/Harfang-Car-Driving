# Mouse flight

import harfang as hg
import math
import random

hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 1280, 720
win = hg.RenderInit('Harfang - Car Driving', res_x, res_y, hg.RF_VSync | hg.RF_MSAA8X)

res = hg.PipelineResources()
pipeline = hg.CreateForwardPipeline()

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# access to compiled resources
hg.AddAssetsFolder('C:/Users/clem/Desktop/Harfang/tutorials-hg2-master/resources_compiled/')

# 2D drawing helpers
vtx_layout = hg.VertexLayoutPosFloatColorFloat()

draw2D_program = hg.LoadProgramFromAssets('shaders/pos_rgb')
draw2D_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Less, hg.FC_Disabled)


def draw_circle(view_id, center, radius, color):
	segment_count = 32
	step = 2 * math.pi / segment_count
	p0 = hg.Vec3(center.x + radius, center.y, 0)
	p1 = hg.Vec3(0, 0, 0)

	vtx = hg.Vertices(vtx_layout, segment_count * 2 + 2)

	for i in range(segment_count + 1):
		p1.x = radius * math.cos(i * step) + center.x
		p1.y = radius * math.sin(i * step) + center.y
		vtx.Begin(2 * i).SetPos(p0).SetColor0(color).End()
		vtx.Begin(2 * i + 1).SetPos(p1).SetColor0(color).End()
		p0.x, p0.y = p1.x, p1.y

	hg.DrawLines(view_id, vtx, draw2D_program, draw2D_render_state)


# gameplay settings
setting_camera_chase_offset = hg.Vec3(0, 2, 0)
setting_camera_chase_distance = 10

setting_car_max_speed = 1
setting_car_speed = 0
setting_car_mouse_sensitivity = 0.5

# setup game world
scene = hg.Scene()
hg.LoadSceneFromAssets('playground/playground.scn', scene, res, hg.GetForwardPipelineInfo())

car_node = hg.CreateInstanceFromAssets(scene, hg.TranslationMat4(hg.Vec3(0, 0.5, 0)), 'voiture/untitled.scn', res, hg.GetForwardPipelineInfo())
camera_node = hg.CreateCamera(scene, hg.TranslationMat4(hg.Vec3(0, 0, -50)), 0.01, 1000)

scene.SetCurrentCamera(camera_node)


def update_car(mouse_x_normd, mouse_y_normd, car_spd):
	if keyboard.Down(hg.K_W):
		car_spd += 0.01
	elif car_spd > 0:
		car_spd -= 0.01
	if keyboard.Down(hg.K_S):
		car_spd -= 0.01
	elif car_spd < 0:
		car_spd += 0.01
	car_spd = hg.Clamp(car_spd, -0.2, setting_car_max_speed)

	car_transform = car_node.GetTransform()

	car_pos = car_transform.GetPos()
	car_pos = car_pos + hg.Normalize(hg.GetZ(car_transform.GetWorld())) * car_spd
	car_pos.y = hg.Clamp(car_pos.y, 0, 50)  # floor/ceiling

	car_rot = car_transform.GetRot()

	next_car_rot = hg.Vec3(car_rot)  # make a copy of the car rotation

	if keyboard.Down(hg.K_Space):
		next_car_rot.y = next_car_rot.y + mouse_x_normd * 0.15
	else:
		next_car_rot.y = next_car_rot.y + mouse_x_normd * 0.06
	

	car_rot = car_rot + (next_car_rot - car_rot) * setting_car_mouse_sensitivity
	if car_spd > 0.03 or car_spd < -0.03:
		car_transform.SetRot(car_rot)
		car_transform.SetPos(car_pos)
	return car_spd


def update_chase_camera(target_pos):
	camera_transform = camera_node.GetTransform()
	camera_to_target = hg.Normalize(target_pos - camera_transform.GetPos())

	camera_transform.SetPos(target_pos - camera_to_target * setting_camera_chase_distance)  # camera is 'distance' away from its target
	camera_transform.SetRot(hg.ToEuler(hg.Mat3LookAt(camera_to_target)))


# game loop
while not keyboard.Down(hg.K_Escape):
	dt = hg.TickClock()  # tick clock, retrieve elapsed clock since last call

	# update mouse/keyboard devices
	keyboard.Update()
	mouse.Update()

	# compute ratio corrected normalized mouse position
	mouse_x, mouse_y = mouse.X(), mouse.Y()

	aspect_ratio = hg.ComputeAspectRatioX(res_x, res_y)
	mouse_x_normd, mouse_y_normd = (mouse_x / res_x - 0.5) * aspect_ratio.x, (mouse_y / res_y - 0.5) * aspect_ratio.y

	# update gameplay elements (car & camera)
	setting_car_speed=update_car(mouse_x_normd, mouse_y_normd, setting_car_speed)
	update_chase_camera(setting_camera_chase_offset * car_node.GetTransform().GetWorld())

	# update scene and submit it to render pipeline
	scene.Update(dt)

	view_id = 0
	view_id, passes_id = hg.SubmitSceneToPipeline(view_id, scene, hg.IntRect(0, 0, int(res_x), int(res_y)), True, pipeline, res)

	# draw 2D GUI
	hg.SetView2D(view_id, res_x, res_y, -1, 1, hg.CF_Depth, hg.Color.Black, 1, 0, True)
	draw_circle(view_id, hg.Vec3(mouse_x, mouse_y, 0), 20, hg.Color.White)  # display mouse cursor

	# end of frame
	hg.Frame()
	hg.UpdateWindow(win)


hg.RenderShutdown()
hg.DestroyWindow(win)

hg.WindowSystemShutdown()
hg.InputShutdown()
