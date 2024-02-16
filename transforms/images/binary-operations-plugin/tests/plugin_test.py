# noqa

import os
import tempfile
import unittest

import cv2
import numpy as np
from bfio import BioReader
from bfio import BioWriter
from polus.plugins.transforms.images.binary_operations import (
    binary_op as binary_operation,
)
from polus.plugins.transforms.images.binary_operations import utils


class PluginData:  # noqa
    def __init__(self):  # noqa
        self.binary_array = np.zeros((100, 100, 1, 1, 1)).astype(np.uint8)
        self.instance_array = np.zeros((100, 100, 1, 1, 1)).astype(np.uint8)
        self.instance_holearray = np.zeros((100, 100, 1, 1, 1)).astype(np.uint8)

        instance_count = 1
        for x1 in range(3, 97, 15):
            for y1 in range(3, 97, 15):
                x2 = min(x1 + 10, 97)
                y2 = min(y1 + 10, 97)

                self.binary_array[x1:x2, y1:y2, 0:1, 0:1, 0:1] = 1
                self.instance_array[x1:x2, y1:y2, 0:1, 0:1, 0:1] = instance_count
                self.instance_holearray[x1:x2, y1:y2, 0:1, 0:1, 0:1] = instance_count
                self.instance_holearray[
                    x1 + 2 : x2 - 2, y1 + 2 : y2 - 2, 0:1, 0:1, 0:1  # noqa
                ] = 0
                instance_count += 1

        self.input_instance_labels = np.unique(self.instance_array)
        self.input_instance_labels = self.input_instance_labels[
            self.input_instance_labels > 0
        ]

        self.input_instance_labels = self.input_instance_labels[
            self.input_instance_labels > 0
        ]
        self.kernel_size = 15
        self.kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.kernel_size, self.kernel_size),
        )


class PluginTest(unittest.TestCase):
    """Tests to ensure the plugin is operating correctly."""

    def test_skeletal(self):  # noqa
        data = PluginData()

        with tempfile.TemporaryDirectory() as tmpdirname:
            # initialize input and output
            input_path = os.path.join(tmpdirname, "input.ome.tif")
            output_path = os.path.join(tmpdirname, "output.ome.tif")

            # get some values into the input!
            with BioWriter(
                input_path,
                backend="python",
                X=100,
                Y=100,
                Z=1,
                C=1,
                T=1,
                dtype=np.uint8,
            ) as bw:
                bw[:] = data.instance_array

            output_path = binary_operation(
                input_path=input_path,
                output_path=output_path,
                function=utils.skeleton_binary,
                operation="skeleton",
                extra_arguments=None,
                extra_padding=data.kernel_size,
                override=False,
            )

            # read the output generated by function
            with BioReader(output_path, backend="python") as br:
                instance_output_array = br[:].squeeze()

        instance_output_labels = np.unique(instance_output_array)
        instance_output_labels = instance_output_labels[instance_output_labels > 0]

        for instance_output_label in instance_output_labels:
            instance_outputSingle_instance = (
                instance_output_label == instance_output_array
            ).astype(np.uint8)
            instance_inputSingle_instance = (
                instance_output_label == data.instance_array.squeeze()
            ).astype(np.uint8)

            contours_output, _ = cv2.findContours(
                instance_outputSingle_instance,
                mode=cv2.RETR_TREE,
                method=cv2.CHAIN_APPROX_NONE,
            )
            contours_input, _ = cv2.findContours(
                instance_inputSingle_instance,
                mode=cv2.RETR_TREE,
                method=cv2.CHAIN_APPROX_NONE,
            )

            for contour_output, contour_input in zip(contours_output, contours_input):
                area_output = cv2.contourArea(contour_output)
                area_input = cv2.contourArea(contour_input)
                assert area_output < area_input

    def test_dilation_erosion_morphologicalgradient(self):  # noqa
        data = PluginData()

        with tempfile.TemporaryDirectory() as tmpdirname:
            # initialize input and outputs
            input_path = os.path.join(tmpdirname, "input.ome.tif")
            output_dilation_path = os.path.join(tmpdirname, "output_dilation.ome.tif")
            output_erosion_path = os.path.join(tmpdirname, "output_erosion.ome.tif")
            output_morphgrad_path = os.path.join(tmpdirname, "output_morphgrad.ome.tif")

            with BioWriter(
                input_path,
                backend="python",
                X=100,
                Y=100,
                Z=1,
                C=1,
                T=1,
                dtype=np.uint8,
            ) as bw:
                bw[:] = data.instance_array

            output_dilation_path = binary_operation(
                input_path=input_path,
                output_path=output_dilation_path,
                function=utils.dilate_binary,
                operation="dilation",
                extra_arguments=1,
                extra_padding=data.kernel_size,
                override=False,
            )
            output_erosion_path = binary_operation(
                input_path=input_path,
                output_path=output_erosion_path,
                function=utils.erode_binary,
                operation="erosion",
                extra_arguments=1,
                extra_padding=data.kernel_size,
                override=False,
            )
            output_morphgrad_path = binary_operation(
                input_path=input_path,
                output_path=output_morphgrad_path,
                function=utils.morphgradient_binary,
                operation="morphological_gradient",
                extra_arguments=None,
                extra_padding=data.kernel_size,
                override=False,
            )

            # read the output generated by function
            with BioReader(output_dilation_path, backend="python") as br:
                instance_output_dilation_array = br[:].squeeze().astype(np.uint8)

            with BioReader(output_erosion_path, backend="python") as br:
                instance_output_erosion_array = br[:].squeeze().astype(np.uint8)

            with BioReader(output_morphgrad_path, backend="python") as br:
                instance_output_morphgrad_array = br[:].squeeze().astype(np.uint8)

        # test dilation
        instance_output_dilation_labels = np.unique(instance_output_dilation_array)
        instance_output_dilation_labels = instance_output_dilation_labels[
            instance_output_dilation_labels > 0
        ]

        assert np.all(data.input_instance_labels == instance_output_dilation_labels)

        # test erosion
        instance_output_erosion_labels = np.unique(instance_output_erosion_array)
        instance_output_erosion_labels = instance_output_erosion_labels[
            instance_output_erosion_labels > 0
        ]

        for instance_output_erosion_label in instance_output_erosion_labels:
            instance_output_erosionSingle_instance = (
                instance_output_erosion_label == instance_output_erosion_array
            ).astype(np.uint8)
            instance_input_erosionSingle_instance = (
                instance_output_erosion_label == data.instance_array.squeeze()
            ).astype(np.uint8)

            contours_output, _ = cv2.findContours(
                instance_output_erosionSingle_instance,
                mode=cv2.RETR_TREE,
                method=cv2.CHAIN_APPROX_NONE,
            )
            contours_input, _ = cv2.findContours(
                instance_input_erosionSingle_instance,
                mode=cv2.RETR_TREE,
                method=cv2.CHAIN_APPROX_NONE,
            )

            for contour_output, contour_input in zip(contours_output, contours_input):
                area_output = cv2.contourArea(contour_output)
                area_input = cv2.contourArea(contour_input)
                assert area_output < area_input

        # test morphological gradient
        diff_dilation_erosion = np.subtract(
            instance_output_dilation_array,
            instance_output_erosion_array,
        )
        assert np.array_equal(diff_dilation_erosion, instance_output_morphgrad_array)

    def test_fillholes(self):  # noqa
        data = PluginData()

        with tempfile.TemporaryDirectory() as tmpdirname:
            # initialize input and output
            input_path = os.path.join(tmpdirname, "input.ome.tif")
            output_path = os.path.join(tmpdirname, "output.ome.tif")

            # get some values into the input!
            with BioWriter(
                input_path,
                backend="python",
                X=100,
                Y=100,
                Z=1,
                C=1,
                T=1,
                dtype=np.uint8,
            ) as bw:
                bw[:] = data.instance_holearray

            output_path = binary_operation(
                input_path=input_path,
                output_path=output_path,
                function=utils.fill_holes_binary,
                operation="fill_holes",
                extra_arguments=None,
                extra_padding=data.kernel_size,
                override=False,
            )

            # read the output generated by function
            with BioReader(output_path, backend="python") as br:
                instance_output_array = br[:].squeeze()

        for input_instance_label in data.input_instance_labels:
            instance_outputSingle_instance = (
                input_instance_label == instance_output_array
            ).astype(np.uint8)
            _, hierarchies = cv2.findContours(
                instance_outputSingle_instance,
                mode=cv2.RETR_TREE,
                method=cv2.CHAIN_APPROX_NONE,
            )
            assert (hierarchies == -1).all()

    def test_opening_and_tophat(self):  # noqa
        data = PluginData()

        with tempfile.TemporaryDirectory() as tmpdirname:
            # initialize input and output
            input_path = os.path.join(tmpdirname, "input.ome.tif")
            output_tophat_path = os.path.join(tmpdirname, "output_tophat.ome.tif")
            output_opening_path = os.path.join(tmpdirname, "output_opening.ome.tif")

            # get some values into the input!
            with BioWriter(
                input_path,
                backend="python",
                X=100,
                Y=100,
                Z=1,
                C=1,
                T=1,
                dtype=np.uint8,
            ) as bw:
                bw[:] = data.instance_array

            output_tophat_path = binary_operation(
                input_path=input_path,
                output_path=output_tophat_path,
                function=utils.tophat_binary,
                operation="top_hat",
                extra_arguments=None,
                extra_padding=data.kernel_size,
                override=False,
            )
            output_opening_path = binary_operation(
                input_path=input_path,
                output_path=output_opening_path,
                function=utils.open_binary,
                operation="opening",
                extra_arguments=None,
                extra_padding=data.kernel_size,
                override=False,
            )

            # read the output generated by function
            with BioReader(output_tophat_path, backend="python") as br:
                instance_output_tophat_array = br[:].squeeze().astype(np.uint8)

            with BioReader(output_opening_path, backend="python") as br:
                instance_output_opening_array = br[:].squeeze().astype(np.uint8)

        instance_output_array = instance_output_tophat_array
        instance_output_array[
            instance_output_opening_array > 0
        ] = instance_output_opening_array[instance_output_opening_array > 0]

        assert np.array_equal(instance_output_array, data.instance_array.squeeze())

    def test_closing_and_blackhat(self):  # noqa
        data = PluginData()

        with tempfile.TemporaryDirectory() as tmpdirname:
            # initialize input and output
            input_path = os.path.join(tmpdirname, "input.ome.tif")
            output_blackhat_path = os.path.join(tmpdirname, "output_blackhat.ome.tif")
            output_closing_path = os.path.join(tmpdirname, "output_closing.ome.tif")

            # get some values into the input!
            with BioWriter(
                input_path,
                backend="python",
                X=100,
                Y=100,
                Z=1,
                C=1,
                T=1,
                dtype=np.uint8,
            ) as bw:
                bw[:] = data.instance_array

            output_blackhat_path = binary_operation(
                input_path=input_path,
                output_path=output_blackhat_path,
                function=utils.blackhat_binary,
                operation="black_hat",
                extra_arguments=None,
                extra_padding=data.kernel_size,
                override=False,
            )
            output_closing_path = binary_operation(
                input_path=input_path,
                output_path=output_closing_path,
                function=utils.close_binary,
                operation="closing",
                extra_arguments=None,
                extra_padding=data.kernel_size,
                override=False,
            )

            # read the output generated by function
            with BioReader(output_blackhat_path, backend="python") as br:
                instance_output_blackhat_array = br[:].squeeze().astype(np.uint8)

            with BioReader(output_closing_path, backend="python") as br:
                instance_output_closing_array = br[:].squeeze().astype(np.uint8)

        instance_output_array = instance_output_blackhat_array
        instance_output_array[
            instance_output_closing_array > 0
        ] = instance_output_closing_array[instance_output_closing_array > 0]

        assert np.array_equal(instance_output_array, data.instance_array.squeeze())

    def test_instance_removelargeobjects(self):  # noqa
        data = PluginData()
        threshold = 80

        with tempfile.TemporaryDirectory() as tmpdirname:
            # initialize input and output
            input_path = os.path.join(tmpdirname, "input.ome.tif")
            output_path = os.path.join(tmpdirname, "output.ome.tif")

            # get some values into the input!
            with BioWriter(
                input_path,
                backend="python",
                X=100,
                Y=100,
                Z=1,
                C=1,
                T=1,
                dtype=np.uint8,
            ) as bw:
                bw[:] = data.instance_array

            output_path = binary_operation(
                input_path=input_path,
                output_path=output_path,
                function=utils.areafiltering_remove_larger_objects_binary,
                operation="filter_area_remove_large_objects",
                extra_arguments=threshold,
                extra_padding=data.kernel_size,
                override=False,
            )

            # read the output generated by function
            with BioReader(output_path, backend="python") as br:
                instance_output_array = br[:].squeeze()

        instance_output_labels = np.unique(instance_output_array)
        instance_output_labels = instance_output_labels[instance_output_labels > 0]

        assert len(instance_output_labels) == 13

        for instance_output_label in instance_output_labels:
            instance_outputSingle_instance = (
                instance_output_label == instance_output_array
            ).astype(np.uint8)
            contours, _ = cv2.findContours(
                instance_outputSingle_instance,
                mode=cv2.RETR_TREE,
                method=cv2.CHAIN_APPROX_NONE,
            )
            for contour in contours:
                area = cv2.contourArea(contour)
                assert area <= threshold

    def test_instance_removesmallobjects(self):  # noqa
        data = PluginData()
        threshold = 80

        with tempfile.TemporaryDirectory() as tmpdirname:
            # initialize input and output
            input_path = os.path.join(tmpdirname, "input.ome.tif")
            output_path = os.path.join(tmpdirname, "output.ome.tif")

            # get some values into the input!
            with BioWriter(
                input_path,
                backend="python",
                X=100,
                Y=100,
                Z=1,
                C=1,
                T=1,
                dtype=np.uint8,
            ) as bw:
                bw[:] = data.instance_array

            output_path = binary_operation(
                input_path=input_path,
                output_path=output_path,
                function=utils.areafiltering_remove_smaller_objects_binary,
                operation="filter_area_remove_small_objects",
                extra_arguments=threshold,
                extra_padding=data.kernel_size,
                override=False,
            )

            # read the output generated by function
            with BioReader(output_path, backend="python") as br:
                instance_output_array = br[:].squeeze()

        instance_output_labels = np.unique(instance_output_array)
        instance_output_labels = instance_output_labels[instance_output_labels > 0]

        assert len(instance_output_labels) == 36

        for instance_output_label in instance_output_labels:
            instance_outputSingle_instance = (
                instance_output_label == instance_output_array
            ).astype(np.uint8)
            contours, _ = cv2.findContours(
                instance_outputSingle_instance,
                mode=cv2.RETR_TREE,
                method=cv2.CHAIN_APPROX_NONE,
            )
            for contour in contours:
                area = cv2.contourArea(contour)
                assert area >= threshold


if __name__ == "__main__":
    unittest.main()
