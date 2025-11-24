#!/bin/bash
# Combined ffmpeg -y commands for all static video wipes with 3-second delay between each

# Initial list wipes
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y horizontal_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeup:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y vertical_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=diagbr:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y diagonal_topleft_bottomright_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=diagbl:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y diagonal_topright_bottomleft_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y circular_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=rectcrop:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y square_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i diamond_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y diamond_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i star_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y star_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i cross_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y cross_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=pixelize:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y checkerboard_wipe.mp4
sleep 3

# Expanded list wipes
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y full_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y circle_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y iris_circle_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y ellipse_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=clock:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y clock_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y reveal_circle_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i triangle_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y triangle_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i triangle_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y reveal_triangle_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y half_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=rectcrop:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y iris_square_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=rectcrop:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y rectangle_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=rectcrop:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y reveal_square_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i star_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y reveal_star_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i heart_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y heart_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i pentagon_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y pentagon_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i hexagon_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y hexagon_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i octagon_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y octagon_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i parallelogram_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y parallelogram_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i chevron_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y chevron_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=diagbr:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y diagonal_linear_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=diagbl:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y split_diagonal_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=radial:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y angular_shutter_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i zigzag_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y zigzag_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i sawtooth_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y sawtooth_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=pixelize:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y grid_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i honeycomb_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y honeycomb_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i starfield_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y starfield_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=pixelize:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y mosaic_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=hlr:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y barn_door_h_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=vud:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y barn_door_v_w

ipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i four_panel_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y four_panel_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=hblur:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y blinds_h_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=vblur:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y blinds_v_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=radial:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y fan_blades_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=clock:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y clock_hands_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=circleopen:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y curved_arc_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i page_curl_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y page_curl_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i flipboard_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y flipboard_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=hblur:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y louver_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i sliding_polygon_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y sliding_polygon_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i fractal_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y fractal_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=pixelize:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y fade_grid_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i cube_spin_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y cube_spin_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i card_flip_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y card_flip_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i polygon_tunnel_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y polygon_tunnel_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i prism_fold_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y prism_fold_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i svg_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y svg_mask_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i text_reveal_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y text_reveal_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i logo_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y logo_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=rectcrop:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y letterboxed_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=radial:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y angular_burst_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i polygon_scatter_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y polygon_scatter_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i blade_slash_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y blade_slash_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=radial:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y rotating_window_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=radial:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y radial_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y bar_h_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeup:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y bar_v_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=hblur:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y venetian_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=vblur:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y window_blind_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=hlr:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y door_h_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=vud:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y door_v_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i page_peel_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y page_peel_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=zoom:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y zoom_in_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=zoom:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y zoom_out_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y push_left_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wiperight:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y push_right_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeup:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y push_up_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipedown:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y push_down_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -filter_complex "[0:v][1:v]xfade=transition=radial:duration=1.0:offset=5,format=yuv420p" -c:v libx264 -y spiral_wipe.mp4
sleep 3
ffmpeg -y -i 0.mp4 -i 1.mp4 -i wave_mask.png -filter_complex "[1:v][2:v]alphamerge[fg];[0:v][fg]overlay=0:0,format=yuv420p" -c:v libx264 -y wave_wipe.mp4