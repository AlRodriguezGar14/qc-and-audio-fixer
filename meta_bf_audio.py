import subprocess
import os
import random
import sys
import time
from colorama import Fore, Back, Style






# For security won't use Shell=True until the next function when everything is ok
# Analysis of the audio levels.
def analysis(what_do, input, source_index, temp_output):
    with open(temp_output, 'w') as f:

        print('\nTime to do some research. I will have all the information in a moment.\nThis can take some minutes, so don not worry. You will have your report ⏳\n')
        
        # I don't want to launch to Shell=True in order to avoid malware (if they introduce something that is not a title, the script will crash). That's why I have to find where in the array is the title. It makes the code uglier and slower to write/scalate/fix, but it's safer.
        what_do['command'][source_index] = input
        
        # Thanks to using Popen, I display the subprocess in the screeen while it is being written at temp_output
        scan = subprocess.Popen(what_do['command'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        # Some commands save the information at stderr and some others at stdout. The only way to know this is testing the code. (this code block can be improved in the future)
        if what_do['output'] == 'stderr':
            for line in scan.stderr:
                sys.stdout.write(line)
                f.write(line)
            scan.wait()
        elif what_do['output'] == 'stdout':
            for line in scan.stdout:
                sys.stderr.write(line)
                f.write(line)
            scan.wait()
        else:
            print(f"{Back.RED}Error{Style.RESET_ALL}, the output information is missing, the information won't be saved.")

        if scan.returncode != 0:
            print(f"{Back.RED}Error{Style.RESET_ALL}")

 

## This is for searching the results of the analyze function
## Currently if the video has two video streams the app crashes here. It's useful because it's a good reminder to delete the timecode track, but crashing the app is never good. I have to understand what happens and fix it in future versions.
def search(list_of_keywords, where_search, where_save):
    for keyword in list_of_keywords:
        # This is to avoid rewritting. Important with the ffprobe code. This way we avoid the audio data (because it comes later) rewritting the video data.
        # It's very importat to know the given outpout in order to make this work.
        if keyword in where_search:
            if where_search != "codec_type = data":
                if keyword in where_save.keys():
                    where_save[f'{keyword}_copy'] = where_search
                else:
                    where_save[keyword] = where_search
            else:
                where_save['timecode_track'] = True
                break


       

def audio_results(read_file):
        # Get the raw information and make it readable
        loudnorm_result = open(read_file, 'r')
        extract_audiolevels = loudnorm_result.readlines()
        for line in extract_audiolevels: 
            if line.__contains__("input_"):
                new_line = line.replace('"', '').replace(':', '=').replace(' ', '').replace('input', 'measured').strip('\t \n ,')
                search([ 'measured_i', 'measured_tp', 'measured_lra', 'measured_thresh'], new_line, audio_levels)
                

        print(f"Audio review: {Back.GREEN}{Fore.BLACK} Success {Style.RESET_ALL}\n")
        os.system(f"rm {read_file}")

        # This is just to print the results in a user friendly way
        printables = [
                ["Integrated", "measured_i"],
                ["True Peak", "measured_tp"],
                ["LRA", "measured_lra"],
                ["Threshold", "measured_thresh"],
                ]
        print_results(printables, audio_levels, has_space=False)



def metadata_results(read_file):
    
    data_results = open(read_file, 'r')
    extract_data = data_results.readlines()
    
    timecode_track_status = f"\n{Back.GREEN}{Fore.BLACK} No timecode track found {Style.RESET_ALL}\n"

    # burn the information in video_data. It's very importat to know the given outpout in order to make this work. Writting the original ffprobe code in order to get only the streams list is not working correctly.
    for line in extract_data:
        new_line = line.strip(' , \t \n').replace('":', ' =').replace('"', '')
        
        search([ 'codec_name', 'codec_type', 'codec_tag_string', 'width', 'height', 'sample_aspect_ratio', 'field_order', 'r_frame_rate', 'color_space', 'color_primaries', 'color_transfer', 'color_range'], new_line, video_data)

        ## We sanitize the code. If there is a data stream we Stop automatically the process.
        if video_data['timecode_track']:
            timecode_track_status = f"\n{Back.RED}{Fore.BLACK} Timecode track found. It will be removed. {Style.RESET_ALL}\n"
            global ffmpeg_audio_fix
            ffmpeg_audio_fix = remove_timecode_and_fix_audio
            break

    print(timecode_track_status)
    
    if video_data['codec_type'] == "codec_type = audio":

        # Remove the temporary file. If we reach here there has not been errors. That means that it is not necessary.    
        os.system(f"rm {read_file}")

        ## When fixing a video with compressor, the audio channel goes before the video channel. That's why I use the values with _copy at the end. 
        ## When they come later I just save them as copy in order to avoid duplications and have more control (The data can be added in any random way depending the output)
        printables = [
        ["Codec Type", "codec_type_copy"],
        ["Codec Name", "codec_name_copy"],
        ["Width", "width"],
        ["Height", "height"],
        ["Codec Tag String", "codec_tag_string_copy"],
        ["Aspect Ratio", "sample_aspect_ratio"],
        ["Field Order", "field_order"],
        ["Frame Rate (in fps)", "r_frame_rate_copy"],
        ["Color Space", "color_space"],
        ["Color Primaries", "color_primaries"], 
        ["Color Transfer", "color_transfer"],
        ["Color Range", "color_range"],
        ]


        try:
# Convert the framerate to the software standard   
            video_data['r_frame_rate_clean'] = round(eval(video_data['r_frame_rate_copy'].removeprefix('r_frame_rate = ')), 3)
            int_of_float = int(video_data['r_frame_rate_clean'])
            if (int_of_float == 30) or (int_of_float == 24) or (int_of_float == 25):
                video_data['r_frame_rate_copy'] = f"r_frame_rate = {int_of_float}"
            else:
                rounded = round(float(video_data['r_frame_rate_clean']), 3)

                video_data['r_frame_rate_copy'] = f"r_frame_rate = {rounded}"
        except:
            print("\nNo data available.\n")
            



        print_results(printables, video_data, has_space=True)  
            


    elif video_data['codec_type'] == "codec_type = video":
        try:
            # Convert the framerate to the software standard   
            video_data['r_frame_rate_clean'] = round(eval(video_data['r_frame_rate'].removeprefix('r_frame_rate = ')), 3)
            int_of_float = int(video_data['r_frame_rate_clean'])
            if (int_of_float == 30) or (int_of_float == 24) or (int_of_float == 25):
                video_data['r_frame_rate'] = f"r_frame_rate = {int_of_float}"
            else:
                rounded = round(float(video_data['r_frame_rate_clean']), 3)

                video_data['r_frame_rate'] = f"r_frame_rate = {rounded}"
                
        except: 
            print("\nNo data available.\n")

        # Remove the temporary file. If we reach here there has not been errors. That means that it is not necessary.    
        os.system(f"rm {read_file}")
        
        printables = [
                ["Codec Type", "codec_type"],
                ["Codec Name", "codec_name"],
                ["Width", "width"],
                ["Height", "height"],
                ["Codec Tag String", "codec_tag_string"],
                ["Aspect Ratio", "sample_aspect_ratio"],
                ["Field Order", "field_order"],
                ["Frame Rate (in fps)", "r_frame_rate"],
                ["Color Space", "color_space"],
                ["Color Primaries", "color_primaries"], 
                ["Color Transfer", "color_transfer"],
                ["Color Range", "color_range"],
                ]

        
        print_results(printables, video_data, has_space=True)




def print_results(printables, dict, has_space):
    print(f"\n{Fore.CYAN}These are the values for {Back.CYAN}{Fore.BLACK} {dict['name']}: {Style.RESET_ALL}\n")
    for element in printables:
        if has_space == True:
            prefix = element[1].removesuffix('_copy') + ' = '
        else:
            prefix = element[1].removesuffix('_copy') + '='

        print(f"\t{element[0]}: {Fore.CYAN}{dict[element[1]].removeprefix(prefix)}{Style.RESET_ALL}")
    print("\n")



# This function fixes the audio. It does let us choose between stereo and dual mono. 
def audio_fix(title, integrated, true_peak, lra, threshold, dual_mono_string, code):
    fixed_output = f"{title.removesuffix('.mov')}_FIXED.mov"
    
    fix_code = code.format(source=title, integrated=integrated, true_peak=true_peak, lra=lra, threshold=threshold, dual_mono=dual_mono_string, fixed_output=fixed_output)

    fix = subprocess.Popen(fix_code, shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    for line in fix.stderr:
        sys.stdout.write(line)
    fix.wait()

def timecode_remover(title, code):
    fixed_output = f"{title.removesuffix('.mov')}_FIXED.mov"
    
    fix_code = code.format(source=title, fixed_output=fixed_output)
    fix = subprocess.Popen(fix_code, shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    for line in fix.stderr:
        sys.stdout.write(line)
    fix.wait


# Check if the video has black frames at top and/or bottom
def black_frame_check(role):
    
    temp_bf_top = f"package_creation_bf_top{n_output}.txt"
    temp_bf_end = f"package_creation_bf_end{n_output}.txt"

    # The code to check the black frames. It is different depending if it's main or preview and if it's top or bottom    
    formulas_top = {'preview': f'ffmpeg -hide_banner -t 6 -i {title} -vf blackframe=amount=100:thresh=17 -f null -',
                'main': f'ffmpeg -hide_banner -t 1 -i {title} -vf blackframe=amount=100:thresh=17 -f null -'}

    formulas_bottom = {'preview': f'ffmpeg -hide_banner -sseof -5 -i {title} -vf blackframe=amount=100:thresh=17 -f null -',
                    'main': f'ffmpeg -hide_banner -sseof -1 -i {title} -vf blackframe=amount=100:thresh=17 -f null -'}


    with open(temp_bf_top, 'w') as f : 
        bf_top = subprocess.Popen(formulas_top[role], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in bf_top.stderr:
            sys.stdout.write(line)
            f.write(line)
        bf_top.wait()
    with open(temp_bf_end, 'w') as f : 
        bf_end = subprocess.Popen(formulas_bottom[role], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in bf_end.stderr:
            sys.stdout.write(line)
            f.write(line)
        bf_end.wait()

    # We get the info from the subprocess and make it readable line by line
    extract_bf_top = open(temp_bf_top, 'r').readlines()
    extract_bf_end = open(temp_bf_end, 'r').readlines()
    top_results= []
    end_results = []

    top_black_frames = False
    for line in extract_bf_top:
        
        if line.__contains__("frame:0"):
            top_black_frames = True
            # We only check how many black frames there are if the very first one is black. If not, it's an auto-fail
        if top_black_frames == True:    
            if line.__contains__("black:100"):
                # We already know what we need to know. 
                # We change all the lines with a black frame for something that we can count (Success word in this case).
                # 1 'Success' means 1 black frame. We only have to count the length of the array.
                new_line = line.replace(line, 'Success')
                top_results.append(new_line)

    if len(top_results) > 0:
        print(f'{Fore.BLACK}{Back.GREEN}\n I found at least {len(top_results)} black frame(s) at the top {Style.RESET_ALL}')
    else:
        print(f"{Fore.BLACK}{Back.RED}\nThe title does't start with a black frame{Style.RESET_ALL}")

    for line in extract_bf_end:
        if line.__contains__("black:100"):
            new_line = line.replace(line, 'Success')
            end_results.append(new_line)

    if len(end_results) > 0:
        print(f'{Fore.BLACK}{Back.GREEN}\n I found at least {len(end_results)} black frame(s) at the end {Style.RESET_ALL}\n')
    else:
        print(f'{Fore.BLACK}{Back.RED}\nNo black frames at the end have been found{Style.RESET_ALL}\n')

    # Remove the unnecessary files (you can read the info on the terminal thanks to subprocess.Popen instead of subprocess.run)
    os.system(f"rm {temp_bf_top}")
    os.system(f"rm {temp_bf_end}")


    
def want_to_analyze(target, function):
    func = {"audio_checker": analysis, 
            "meta_checker": analysis}
    params = {"audio_checker": [audiocheck, title, 2, temp_output], 
            "meta_checker":[datacheck, title, 7, temp_output]}

    while True:
        question = input_validator(f"Do you want to analyze the {target}? y/n", "yes", "y", "no", "n")
        time.sleep(0.2)
        if question:
            func[function](*params[function])
            if target == "audio":
                audio_results(temp_output)
                global audio_analyzed
                audio_analyzed = True

            if target == "video metadata":
                metadata_results(temp_output)
                global video_meta_analyzed
                video_meta_analyzed = True

            else:
                break
            break

        else:
            break


def input_validator(question, *options):
    while True:
        variable = input(f"\n{question}\n").lower()
        if variable in options:
            if variable == 'y':
                choice = True
                return choice
            elif variable == 'n':
                choice = False
                return choice
            else:
                return variable

        else:
            print(f"Sorry, I did not understand use one of these commands {options}")




if __name__ == '__main__':


    # This is a magic number, but I want to avoid the Shell=True at the beginning, so,
    # index for analysis function is 2
    audiocheck = {'command': ['ffmpeg', '-i', 'SOURCE', '-vn', '-filter:a', 'loudnorm=print_format=json', '-f', 'null', '-',], 'output': 'stderr'}

    # index for analysis function is 7
    datacheck = {'command': ['ffprobe', '-hide_banner', '-loglevel', 'warning', '-print_format', 'json', '-show_streams',  'source', ], 'output': 'stdout'}


    ffmpeg_audio_fix = 'ffmpeg -i {source} -c:v copy -colorspace bt709 -color_primaries bt709 -color_trc bt709 -movflags write_colr -c:a pcm_s24le -ar 48k -filter:a loudnorm=i=-24.0:tp=-6:print_format=summary:{integrated}:{true_peak}:{lra}:{threshold}:{dual_mono} {fixed_output}' 

    only_remove_timecode_track = 'ffmpeg -i {source} -dn -map_metadata -1 -metadata:s:v encoder="Apple ProRes 422 HQ" -fflags bitexact -write_tmcd 0 -vendor abm0 -c copy {fixed_output}'

    remove_timecode_and_fix_audio = 'ffmpeg -i {source} -dn -map_metadata -1 -metadata:s:v encoder="Apple ProRes 422 HQ" -fflags bitexact -write_tmcd 0 -vendor abm0 -c:v copy -colorspace bt709 -color_primaries bt709 -color_trc bt709 -movflags write_colr -c:a pcm_s24le -ar 48k -filter:a loudnorm=i=-24.0:tp=-6:print_format=summary:{integrated}:{true_peak}:{lra}:{threshold}:{dual_mono} {fixed_output}' 



    # The dictionary where the clean information goes
    audio_levels = {'name':'audio levels'}
    audio_analyzed = False

    # The dictionary with the metadata info
    video_data = {'name':'video metadata', 'timecode_track':False, 'timecode_fix':False}
    video_meta_analyzed = False
    # This file is where I move all the information that ffmpeg prints to the console
    # later it's going to be deleted, that's why I use a random generated number (not to remove anything useful)
    n_output = random.randint(99999999, 99999999999)
    temp_output = f"package_creation_audiolevels{n_output}.txt"



        # THE APP STARTS INTERACTING HERE.
    print("\nBefore we start I need some information.\n")

    title = input("Drag your file here: ").replace(' ', '')
    main_prev = input_validator("Is your title main[m] or preview[p]?", "main", "m", "preview", "p")
    stereo_or_dm = input_validator("Is your title stereo[s] or dual mono[dm]?", "stereo", "s", "dual mono", "dm")

    if (main_prev == "m") or (main_prev == "main"):
        main_prev = "main"
    else:
        main_prev = "preview"

    if (stereo_or_dm == "s") or (stereo_or_dm == "stereo"):
        stereo_or_dm = "stereo"
    else:
        stereo_or_dm = "dual mono"

    print(f"\n\t{Fore.CYAN}The video role is:{Style.RESET_ALL} {main_prev}\n\t{Fore.CYAN}The audio is:{Style.RESET_ALL} {stereo_or_dm}\n\t{Fore.CYAN}The location is:{Style.RESET_ALL} {title}")

    print("\nWe are ready to start.\n")
    
    time.sleep(0.2)


    # Function to ask if the user wants to check the video metadata
    want_to_analyze("video metadata", "meta_checker")

    
    # Function to ask if the user wants to check for black frames
    bf_check = input_validator("Do you want to search for black frames? y/n", "yes", "y", "no", "n")
    if bf_check:
        time.sleep(0.2)
        black_frame_check(main_prev)


    # Function to ask if the user wants to check the audio
    want_to_analyze("audio", "audio_checker")
    if audio_analyzed == True:

        want_fix_audio = input_validator("Do you want to fix the audio? y/n", "yes", "y", "no", "n")
        if want_fix_audio:
            time.sleep(0.2)
            # Fix the audio. The code varies depending if the video is stereo or dual mono
            if stereo_or_dm == "stereo":
                audio_fix(title, audio_levels['measured_i'], audio_levels['measured_tp'], audio_levels['measured_lra'], audio_levels['measured_thresh'], "dual_mono=false", ffmpeg_audio_fix)
            elif stereo_or_dm == "dual mono":
                audio_fix(title, audio_levels['measured_i'], audio_levels['measured_tp'], audio_levels['measured_lra'], audio_levels['measured_thresh'], "dual_mono=true", ffmpeg_audio_fix)
            video_data['timecode_track'] = False
        else:
            print("Ok, I won't fix the audio\n")
            time.sleep(0.2)

    if video_data['timecode_track']:
        print("Removing the timecode track...")
        time.sleep(0.5)
        timecode_remover(title, only_remove_timecode_track)
        video_data['timecode_track'] = False


    print("Review Ended")
    input("Press intro to end the session. \n")
    exit

