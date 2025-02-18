Street_View.py for generating images/n
Upscale.vbs for upscaling (optional)
ffmpeg -framerate 30 -i .\output\image_%%06d.png -vf "fps=60,tblend=all_mode=average" -an -c:v libx264 -crf 18 -preset veryslow -y raw.mp4 generate raw with street view, raw2 and raw3 for map view
ffmpeg -y -i raw2.mp4 -i raw3.mp4 -filter_complex vstack=inputs=2 -c:v libx264 -crf 18 -preset ultrafast -pix_fmt yuv420p vstack.mp4
ffmpeg -y -i raw.mp4 -i vstack.mp4 -filter_complex "[0:v]scale=2560x2160[a],[1:v]scale=1280x2160[b1],[a][b1]hstack=inputs=2,fps=24" -an -c:v libx264 -crf 21 -preset veryslow -pix_fmt yuv420p output_side_by_side.mp4
