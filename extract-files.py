#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixup_remove,
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'hardware/qcom-caf/sm8150',
    'hardware/qcom-caf/wlan',
    'hardware/xiaomi',
    'vendor/qcom/opensource/commonsys/display',
    'vendor/qcom/opensource/commonsys-intf/display',
    'vendor/qcom/opensource/dataservices',
    'vendor/qcom/opensource/display',
    'vendor/xiaomi/sweet',
]


def lib_fixup_vendor_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_{partition}' if partition == 'vendor' else None


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'com.qualcomm.qti.dpm.api@1.0',
        'libmmosal',
        'vendor.qti.hardware.fm@1.0',
        'vendor.qti.imsrtpservice@3.0',
        'vendor.qti.hardware.wifidisplaysession@1.0',
    ): lib_fixup_vendor_suffix,
    (
        'libwpa_client',
    ): lib_fixup_remove,
}

blob_fixups: blob_fixups_user_type = {
    'system_ext/bin/wfdservice64': blob_fixup()
        .add_needed('libwfdservice_shim.so'),
    'system_ext/etc/init/wfdservice.rc': blob_fixup()
        .regex_replace(r'(start|stop) wfdservice\b', r'\1 wfdservice64'),
    'system_ext/lib64/libwfdnative.so': blob_fixup()
        .remove_needed('android.hidl.base@1.0.so'),
    'system_ext/lib64/libwfdservice.so': blob_fixup()
        .replace_needed('android.media.audio.common.types-V2-cpp.so', 'android.media.audio.common.types-V4-cpp.so'),
     'vendor/etc/init/init.batterysecret.rc': blob_fixup()
        .regex_replace(' +seclabel u:r:batterysecret:s0\n', ''),
     'vendor/etc/init/init.mi_thermald.rc': blob_fixup()
        .regex_replace(' +seclabel u:r:mi_thermald:s0\n', ''),
     'vendor/lib64/camera/components/com.qti.node.watermark.so': blob_fixup()
        .add_needed('libpiex_shim.so'),
     ('vendor/lib64/mediadrm/libwvdrmengine.so', 'vendor/lib64/libwvhidl.so'): blob_fixup()
        .add_needed('libcrypto_shim.so'),
        ('vendor/lib64/libalLDC.so', 'vendor/lib64/libalhLDC.so'): blob_fixup()
         .clear_symbol_version('AHardwareBuffer_allocate')
         .clear_symbol_version('AHardwareBuffer_describe')
         .clear_symbol_version('AHardwareBuffer_lock')
         .clear_symbol_version('AHardwareBuffer_release')
         .clear_symbol_version('AHardwareBuffer_unlock'),
     ('vendor/lib64/libarcsoft_hta.so', 'vendor/lib64/libarcsoft_super_night_raw.so', 'vendor/lib64/libhvx_interface.so', 'vendor/lib64/libmialgo_rfs.so'): blob_fixup()
         .clear_symbol_version('remote_handle_close')
         .clear_symbol_version('remote_handle_invoke')
         .clear_symbol_version('remote_handle_open')
         .clear_symbol_version('remote_handle64_close')
         .clear_symbol_version('remote_handle64_invoke')
         .clear_symbol_version('remote_handle64_open')
         .clear_symbol_version('remote_register_buf_attr')
         .clear_symbol_version('remote_register_buf')
         .clear_symbol_version('rpcmem_alloc')
         .clear_symbol_version('rpcmem_free')
         .clear_symbol_version('rpcmem_to_fd'),
}  # fmt: skip

module = ExtractUtilsModule(
    'sweet',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module.vendor)
    utils.run()
