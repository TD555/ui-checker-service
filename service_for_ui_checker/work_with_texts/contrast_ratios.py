from sklearn.cluster import KMeans
import cv2


class ContrastCheck:
    def __init__(self, image, texts):
        self.image = image
        self.texts = texts
        
    async def get_CR(self, dominant_color_rgb):

        L = [(0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]) / 255 for color in dominant_color_rgb]
        CR = (max(L) + 0.05) / (min(L) + 0.05)

        return CR

    async def get_colors(self, image_rgb):
        pixels = image_rgb.reshape((-1, 3))

        kmeans = KMeans(n_clusters=2, n_init=10)

        kmeans.fit(pixels)

        dominant_color_rgb = kmeans.cluster_centers_
        return list(dominant_color_rgb)


    async def contrast_ratio(self):

        all_ratios = []

        for item in self.texts:
            
            cropped_image = self.image[item['row_min']:item['row_max'], int(item['column_min'] + 0.2 * item['width']) :item['column_max']]
            main_colors = await self.get_colors(cropped_image)
            all_ratios.append(dict({"contrast_ratio" : await self.get_CR(main_colors)}, **(item)))
            
        return all_ratios
