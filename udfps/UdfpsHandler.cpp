/*
 * Copyright (C) 2022-2024 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#define LOG_TAG "UdfpsHandler.xiaomi_sm6150"

#include "UdfpsHandler.h"

#include <aidl/android/hardware/biometrics/fingerprint/BnFingerprint.h>
#include <android-base/logging.h>
#include <android-base/unique_fd.h>
#include <fcntl.h>
#include <poll.h>
#include <unistd.h>
#include <thread>

// Fingerprint hwmodule commands
#define COMMAND_NIT 10
#define PARAM_NIT_UDFPS 1
#define PARAM_NIT_NONE 0

// Touchfeature
#define TOUCH_DEV_PATH "/dev/xiaomi-touch"
#define TOUCH_UDFPS_ENABLE 10
#define TOUCH_MAGIC 0x5400
#define TOUCH_IOC_SETMODE TOUCH_MAGIC + 0
#define UDFPS_STATUS_ON 1
#define UDFPS_STATUS_OFF -1

#define FOD_UI_PATH "/sys/devices/platform/soc/soc:qcom,dsi-display/fod_ui"

using ::aidl::android::hardware::biometrics::fingerprint::AcquiredInfo;

static bool readBool(int fd) {
    char c;
    int rc;

    rc = lseek(fd, 0, SEEK_SET);
    if (rc) {
        LOG(ERROR) << "failed to seek fd, err: " << rc;
        return false;
    }

    rc = read(fd, &c, sizeof(char));
    if (rc != 1) {
        LOG(ERROR) << "failed to read bool from fd, err: " << rc;
        return false;
    }

    return c != '0';
}

class XiaomiUdfpsHandler : public UdfpsHandler {
  public:
    void init(fingerprint_device_t* device) {
        mDevice = device;
        touch_fd_ = android::base::unique_fd(open(TOUCH_DEV_PATH, O_RDWR));

        std::thread([this]() {
            int fd = open(FOD_UI_PATH, O_RDONLY);
            if (fd < 0) {
                LOG(ERROR) << "failed to open fd, err: " << fd;
                return;
            }

            struct pollfd fodUiPoll = {
                    .fd = fd,
                    .events = POLLERR | POLLPRI,
                    .revents = 0,
            };

            while (true) {
                int rc = poll(&fodUiPoll, 1, -1);
                if (rc < 0) {
                    LOG(ERROR) << "failed to poll fd, err: " << rc;
                    continue;
                }

                mDevice->extCmd(mDevice, COMMAND_NIT,
                                readBool(fd) ? PARAM_NIT_UDFPS : PARAM_NIT_NONE);
            }
        }).detach();
    }

    void onFingerDown(uint32_t /*x*/, uint32_t /*y*/, float /*minor*/, float /*major*/) {
        // nothing
    }

    void onFingerUp() {
        // nothing
    }

    void onAcquired(int32_t result, int32_t vendorCode) {
        if (static_cast<AcquiredInfo>(result) == AcquiredInfo::GOOD) {
            int arg[2] = {TOUCH_UDFPS_ENABLE, UDFPS_STATUS_OFF};
            ioctl(touch_fd_.get(), TOUCH_IOC_SETMODE, &arg);
        } else if (vendorCode == 21 || vendorCode == 23) {
            /*
             * vendorCode = 21 waiting for fingerprint authentication
             * vendorCode = 23 waiting for fingerprint enroll
             */
            int arg[2] = {TOUCH_UDFPS_ENABLE, UDFPS_STATUS_ON};
            ioctl(touch_fd_.get(), TOUCH_IOC_SETMODE, &arg);
        }
    }

    void cancel() {
        int arg[2] = {TOUCH_UDFPS_ENABLE, UDFPS_STATUS_OFF};
        ioctl(touch_fd_.get(), TOUCH_IOC_SETMODE, &arg);
    }

  private:
    fingerprint_device_t* mDevice;
    android::base::unique_fd touch_fd_;
};

static UdfpsHandler* create() {
    return new XiaomiUdfpsHandler();
}

static void destroy(UdfpsHandler* handler) {
    delete handler;
}

extern "C" UdfpsHandlerFactory UDFPS_HANDLER_FACTORY = {
        .create = create,
        .destroy = destroy,
};
