import os
from pcap import chunkDetect

from model import  multi_model

def pcap_to_chunk():
    pcap_directory = "data/A1/PCAP_FILES"
    out_path = "output/chunk/A1"
    for filename in os.listdir(pcap_directory):
        if filename.endswith('.pcap'):
            pcap_file = os.path.join(pcap_directory, filename)
            stream_map = chunkDetect.chunk_detect(pcap_file)
            outfile = out_path + "/chunk_" + filename.replace('.pcap', '.txt')
            chunkDetect.save_chunk(stream_map, outfile)


if __name__ == "__main__":
    pcap_to_chunk()
    # multi_model.train_final_model()
    # multi_model.train_multiple_models()
    # multi_model.test_final_models()


