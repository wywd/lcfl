import time
import cv2 as cv
import numpy as np


# 整个过程不复杂，就省略封装过程了，全部写在ma in中
# 测试平均耗时约1.35s，如果注释掉print/imshow/绘图相关操作，耗时约650ms
if __name__ == '__main__':
    start = time.time()
    #  依次读入护照在可见光，红外光和紫外光下的图片
    image_VIS = cv.imread("img.jpg")
    if image_VIS is None:
        print("载入可见光图片失败")
        exit(-1)
    image_IR = cv.imread("img2.jpg")
    if image_IR is None:
        print("载入红外光图片失败")
        exit(-1)
    image_UV = cv.imread("img3.jpg")
    if image_UV is None:
        print("载入紫外光图片失败")
        exit(-1)
    # 开始鉴伪
    print("第一步：红外光下人脸图像鉴伪")
    face_cascade = cv.CascadeClassifier("haarcascade_frontalface_default.xml")  # 导入xml文件
    if face_cascade is None:
        print("文件名或文件路径错误！")
        exit(-1)
    roi_right_IR = image_IR[:, int(image_IR.shape[1] / 2):]  # 只考虑右半部分是否有人脸，减少计算量
    gray_right_IR = cv.cvtColor(roi_right_IR, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(  # 进行人脸检测
        gray_right_IR,
        scaleFactor=1.2,
        minNeighbors=2,
        minSize=(50, 50),
        maxSize=(160, 160),
        flags=cv.IMREAD_GRAYSCALE
        # flags=cv.CASCADE_SCALE_IMAGE
    )
    if len(faces) == 0:
        print("没有在右半部分检测到人脸，鉴伪通过！")
    else:
        print("在右半部分检测到{0}个人脸，鉴伪失败！".format(len(faces)))
        res = gray_right_IR.copy()
        for (x, y, w, h) in faces:
            cv.rectangle(res, (x, y), (x + w, y + w), (0, 0, 255), 2)
        cv.imshow("res", res)
        exit(-1)
    print("\n---------------------------\n")
    print("第二步：红外光下护照号码鉴伪")
    roi_identity_IR = image_IR[40:65, 332:448]  # 大小为 22×116，这里按照论文直接粗提取
    gray_identity_IR = cv.cvtColor(roi_identity_IR, cv.COLOR_BGR2GRAY)
    blur_identity_IR = cv.GaussianBlur(gray_identity_IR, (5, 5), 0)
    # 采用大津法进行阈值分割，并进行颜色反转
    threshold, binary_identity_IR \
        = cv.threshold(blur_identity_IR, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
    print("护照号码二值化最佳阈值为：", threshold)
    cv.imshow("binary_identity_IR", binary_identity_IR)
    binary_sum = np.sum(binary_identity_IR/255, axis=1)  # 统计水平投影的文字像素值累积和，注意要先转换为0-1值
    print("水平投影后字符像素统计：", binary_sum)
    # 经验设置的一些阈值
    h, w = binary_identity_IR.shape
    sum_thresh = w / 5  # 像素值统计高于该值的行记入字符宽度
    v_upper = h / 2  # 字符投影宽度上限
    v_lower = h / 5  # 字符投影宽度下限
    print("预设像素值阈值：", sum_thresh)
    print("预设字符投影宽度上限：", v_upper)
    print("预设字符投影宽度下限：", v_lower)
    character_width = np.sum(binary_sum > sum_thresh)  # 计算统计得到的字符宽度
    print("统计实际字符投影宽度：", character_width)
    if v_lower < character_width < v_upper:
        print("投影宽度符合要求，鉴伪通过！")
    else:
        print("投影宽度不符合要求，鉴伪失败！")
        exit(-1)
    print("\n---------------------------\n")
    print("第三步：紫外光下护照号码防伪")
    roi_identity_UV = image_UV[40:65, 332:448]  # 大小为 22×116，同样也是粗提取得到的
    blur_identity_UV = cv.GaussianBlur(roi_identity_UV, (5, 5), 0)
    roi_hsv_UV = cv.cvtColor(blur_identity_UV, cv.COLOR_BGR2HSV)
    cv.imshow("roi_hsv_UV", roi_hsv_UV)
    #  紫外光下和红外光下不同，需要先根据颜色进行分割
    lower_red = np.array([156, 43, 46])
    upper_red = np.array([180, 255, 255])
    mask1 = cv.inRange(roi_hsv_UV, lower_red, upper_red)
    lower2_red = np.array([0, 43, 46])
    upper2_red = np.array([10, 255, 255])
    mask2 = cv.inRange(roi_hsv_UV, lower2_red, upper2_red)
    mask = mask1 + mask2
    res = cv.bitwise_and(blur_identity_UV, blur_identity_UV, mask=mask)  # 提取原条纹图掩模区域像素
    gray_identity_UV = cv.cvtColor(res, cv.COLOR_BGR2GRAY)
    threshold, binary_identity_UV = cv.threshold(gray_identity_UV,  0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)  # 阈值分割
    print("护照号码二值化最佳阈值：", threshold)
    cv.imshow("binary_identity_UV", binary_identity_UV)
    binary_sum = np.sum(binary_identity_UV/255, axis=1)
    print("水平投影后字符像素统计：", binary_sum)
    character_width = np.sum(binary_sum > sum_thresh)  # 统计字符宽度
    print("统计实际字符投影宽度：", character_width)
    if v_lower < character_width < v_upper:
        print("投影宽度符合要求，鉴伪通过！")
    else:
        print("投影宽度不符合要求，鉴伪失败！")
        exit(-1)
    print("\n---------------------------\n")
    print("第四步：紫外光下条纹鉴伪")
    roi_stripe_UV = image_UV[170:270, :]  # 同样根据原论文，直接粗提取
    # 转换到HSV空间提取红色亮条纹
    roi_stripe_hsv_UV = cv.cvtColor(roi_stripe_UV, cv.COLOR_BGR2HSV)
    mask1 = cv.inRange(roi_stripe_hsv_UV, lower_red, upper_red)
    mask2 = cv.inRange(roi_stripe_hsv_UV, lower2_red, upper2_red)
    mask = mask1 + mask2
    res = cv.bitwise_and(roi_stripe_UV, roi_stripe_UV, mask=mask)
    gray_stripe_UV = cv.cvtColor(res, cv.COLOR_BGR2GRAY)  # 将提取到的条纹图转换为灰度图，然后进行平滑操作
    cv.imshow("gray_stripe_UV", gray_stripe_UV)
    blur_strip_UV = cv.blur(gray_stripe_UV, (3, 3))
    threshold, binary_stripe_UV = cv.threshold(blur_strip_UV,  0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
    print("亮红色条纹二值化最佳阈值：", threshold)
    #  这里的match.jpg就是从论文中裁剪出来的作者提取出来的红色条纹图，
    #  我把它作为模板，用来进行后面的ORB匹配算法
    img_stripe_match = cv.imread("match.jpg", cv.IMREAD_GRAYSCALE)
    blur_stripe_match = cv.blur(img_stripe_match, (3, 3))
    threshold, binary_stripe_match = cv.threshold(blur_stripe_match, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    print("条纹模板二值化最佳阈值：", threshold)

    orb = cv.ORB.create()  # 使用ORB算法进行角点检测和特征点匹配
    kp1, des1 = orb.detectAndCompute(binary_stripe_UV, None)
    kp2, des2 = orb.detectAndCompute(binary_stripe_match, None)
    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=False)  # 使用汉明距离，不使用交叉验证
    matches = bf.knnMatch(des1, des2, 2)  # 使用KNN算法进行最近领匹配,得到两个最近邻匹配描述符
    print("条纹图特征点个数：{0}, 条纹模板特征点个数：{1}, 最终匹配点数;{2} ".format(len(kp1), len(kp2), len(matches)))
    good = []
    for m, n in matches:  # 筛选好的匹配点
        if m.distance < 0.8 * n.distance:  # 建议比例因子设置为0.7到0.8的范围
            good.append(m)
    print("预设好的匹配点数阈值：9")
    print("好的匹配点个数：", len(good))
    if len(good) > 9:  # 这里根据经验设置一个阈值，如果好的匹配点超过阈值，则说明匹配，画出匹配结果
        print("红色亮条纹匹配成功，鉴伪通过！")
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()
        result = cv.drawMatches(binary_stripe_UV, kp1, binary_stripe_match, kp2, good,
                                None, matchesMask=matchesMask, flags=0)
        cv.imshow("result", result)
    else:
        print("红色亮条纹匹配不成功，鉴伪失败！")
        exit(-1)

    end = time.time()
    print("总运行时间：{:.2f}秒".format(end-start))
    print("\n--------------------\n四步都通过，说明护照鉴伪为真！\n--------------------")
    print("按下空格退出")
    cv.waitKey(0)
    cv.destroyAllWindows()

