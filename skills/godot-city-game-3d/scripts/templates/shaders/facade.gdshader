shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

// Draws storeys and windows procedurally on a plain box.
//
// This is the trick that makes a batched city look built. Every building is the
// same unit cube, scaled by its instance transform, so they all live in one
// MultiMesh and cost one draw call per typology. Detail comes from the shader
// reading each instance's real dimensions and laying out a window grid in
// METRES -- which is why a 12 m rowhouse and a 160 m tower get windows the same
// size instead of the same *number* of windows stretched to fit.
//
// Per-instance data arrives as INSTANCE_CUSTOM = (width, height, depth, seed).
// A height of 0 marks a decorative cap (roofs), which gets no windows.

uniform float floor_height = 3.4;
uniform float window_pitch = 3.0;
uniform vec3 window_color : source_color = vec3(0.06, 0.07, 0.09);
uniform vec3 lit_color : source_color = vec3(1.0, 0.86, 0.58);
// Driven by a day/night system: 0 = daylight, 1 = windows lit.
uniform float night : hint_range(0.0, 1.0) = 0.0;
uniform float wall_roughness : hint_range(0.0, 1.0) = 0.85;
// The generator sinks each box by this much so hillside buildings have a
// foundation. Everything below it is underground and must stay blank.
uniform float foundation = 8.0;

varying vec3 v_local;
varying flat vec3 v_lnormal;
varying flat vec4 v_dims;

void vertex() {
	v_local = VERTEX;
	v_lnormal = NORMAL;
	v_dims = INSTANCE_CUSTOM;
}

float hash21(vec2 p) {
	return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453);
}

void fragment() {
	vec3 base = COLOR.rgb;
	float win = 0.0;
	float lit = 0.0;

	// Skip roof caps, and skip the top and bottom faces -- a window in a roof
	// reads instantly as a bug.
	if (v_dims.y > 0.5 && abs(v_lnormal.y) < 0.5) {
		// The cube spans -0.5..0.5 locally; multiplying by the instance's real
		// size converts that to metres up and along the facade.
		float up = (v_local.y + 0.5) * v_dims.y;
		float across = (abs(v_lnormal.x) > 0.5)
			? (v_local.z + 0.5) * v_dims.z
			: (v_local.x + 0.5) * v_dims.x;

		float storey = floor(up / floor_height);
		float bay = floor(across / window_pitch);
		vec2 f = vec2(fract(across / window_pitch), fract(up / floor_height));

		win = step(0.2, f.x) * step(f.x, 0.8) * step(0.25, f.y) * step(f.y, 0.85);
		// No windows below street level, and none in the ground-floor band --
		// a blank base is what makes the building sit on the pavement.
		win *= step(foundation + 1.0, up);

		// A stable per-window random from (bay, storey, instance seed): the same
		// windows stay lit frame to frame instead of flickering.
		lit = win * night * step(0.55, hash21(vec2(bay, storey) + v_dims.w * 37.0));
	}

	ALBEDO = mix(base, window_color, win);
	ROUGHNESS = mix(wall_roughness, 0.15, win);
	METALLIC = win * 0.2;
	EMISSION = lit_color * lit * 2.0;
}
