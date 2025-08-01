// rustimport:pyo3

//: [dependencies]
//: anyhow = "1.0.98"
//: mnllib = "0.1.0"
//: endian-num = "0.2.0"
//: pyo3 = { version = "0.25.1", features = ["extension-module", "anyhow"] }

use std::io::{self, Cursor};

use endian_num::le16;

use mnllib::{
    consts::STANDARD_DATA_WITH_OFFSET_TABLE_ALIGNMENT,
    map::{FieldMapChunk, FieldMaps},
    misc::{DataWithOffsetTable, Bgr555},
    utils::AlignToElements,
};
use pyo3::{prelude::*, types::PyByteArray};

#[pyfunction]
fn modify_maps(
    py: Python<'_>,
    fmapdata: &[u8],
    treasure_info: &[u8],
    overlay3: &Bound<'_, PyByteArray>,
    overlay4: &Bound<'_, PyByteArray>,
    mario_pal_2: &[u8],
    luigi_pal_2: &[u8],
) -> anyhow::Result<Vec<u8>> {
    let mut field_maps = FieldMaps::from_files(
        fmapdata,
        treasure_info,
        Cursor::new(unsafe { overlay3.as_bytes() }),
        Cursor::new(unsafe { overlay4.as_bytes() }),
    )?;
    py.allow_threads(|| -> anyhow::Result<()> {
        let bowser_map_chunk_data = field_maps.fmapdata_chunks[field_maps.maps[0x001B].map_chunk_index]
            .make_uncompressed(false)?;
        let mut bowser_map_chunk = FieldMapChunk::try_from(DataWithOffsetTable::from_reader(
            &bowser_map_chunk_data[..],
        )?)?;

        let palette = bowser_map_chunk.palettes[0]
            .as_mut()
            .expect("map 0x001B should always have palette 0");

        for n in 0..5 { palette.0[0xC2 + n] = Bgr555::from_bits(le16::from_le_bytes([luigi_pal_2[8 - (n * 2)], luigi_pal_2[8 - (n * 2) + 1]])) }
        for n in 0..5 { palette.0[0xC7 + n] = Bgr555::from_bits(le16::from_le_bytes([mario_pal_2[n * 2], mario_pal_2[(n * 2) + 1]])) }

        bowser_map_chunk_data.clear();
        DataWithOffsetTable::try_from(bowser_map_chunk)?.to_writer(
            &mut *bowser_map_chunk_data,
            Some(STANDARD_DATA_WITH_OFFSET_TABLE_ALIGNMENT),
            false,
        )?;
        bowser_map_chunk_data.align_to_elements(STANDARD_DATA_WITH_OFFSET_TABLE_ALIGNMENT);
        field_maps.fmapdata_chunks[field_maps.maps[0x001B].map_chunk_index].make_compressed()?;
        Ok(())
    })?;
    let mut fmapdata: Vec<u8> = Vec::new();
    let mut treasure_info = io::sink();
    field_maps.to_files(
        &mut fmapdata,
        &mut treasure_info,
        Cursor::new(unsafe { overlay3.as_bytes_mut() }),
        Cursor::new(unsafe { overlay4.as_bytes_mut() }),
        true,
    )?;
    Ok(fmapdata)
}
